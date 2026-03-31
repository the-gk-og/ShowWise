from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_mail import Mail, Message
from flask_cors import CORS
from dotenv import load_dotenv
import os, json, requests

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'fallback-secret-key')

# CORS setup
CORS(app, resources={r"/api/*": {"origins": "*", "methods": ["GET", "OPTIONS"], "allow_headers": ["Content-Type"]}})

# Mail config
app.config.update(
    MAIL_SERVER=os.getenv('MAIL_SERVER'),
    MAIL_PORT=int(os.getenv('MAIL_PORT', 587)),
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv('MAIL_USERNAME'),
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD'),
    MAIL_DEFAULT_SENDER=os.getenv('MAIL_DEFAULT_SENDER')
)
mail = Mail(app)

# Path to email templates folder
EMAIL_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), 'email_templates')

# Cloudflare Turnstile
TURNSTILE_SECRET     = os.getenv('CLOUDFLARE_TURNSTILE_SECRET', '')
TURNSTILE_VERIFY_URL = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'


# ==================== TURNSTILE ====================

def verify_turnstile(token: str, remote_ip: str = '') -> bool:
    """Verify a Cloudflare Turnstile token server-side.
    Returns True if valid, False otherwise.
    If CLOUDFLARE_TURNSTILE_SECRET is not set, skips verification (dev mode).
    """
    if not TURNSTILE_SECRET:
        print("Warning: CLOUDFLARE_TURNSTILE_SECRET not set - skipping Turnstile verification")
        return True
    if not token:
        return False
    try:
        resp = requests.post(TURNSTILE_VERIFY_URL, data={
            'secret':   TURNSTILE_SECRET,
            'response': token,
            'remoteip': remote_ip,
        }, timeout=5)
        result = resp.json()
        return result.get('success', False)
    except Exception as e:
        print(f"Turnstile verification error: {e}")
        return False


# ==================== EMAIL HELPERS ====================

def load_email_template(name: str, context: dict) -> str:
    """Load an HTML email template and substitute {{ key }} placeholders."""
    path = os.path.join(EMAIL_TEMPLATES_DIR, name)
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()
    for key, value in context.items():
        html = html.replace('{{ ' + key + ' }}', str(value) if value else '')
        html = html.replace('{{' + key + '}}', str(value) if value else '')
    return html


def send_html_email(subject: str, recipient: str, html_body: str, text_body: str = ''):
    """Send an HTML email with an optional plain-text fallback."""
    msg = Message(subject, recipients=[recipient])
    msg.html = html_body
    if text_body:
        msg.body = text_body
    mail.send(msg)


# ==================== BACKEND API ====================

def load_organizations():
    try:
        backend_url = os.getenv('BACKEND_API_URL', '').rstrip('/')
        backend_key = os.getenv('BACKEND_API_KEY', '')
        if not backend_url or not backend_key:
            print("Warning: BACKEND_API_URL or BACKEND_API_KEY not configured")
            return {}
        response = requests.get(
            f"{backend_url}/api/organizations",
            headers={'X-API-Key': backend_key, 'Content-Type': 'application/json'},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return data.get('organizations', {}) if data.get('success') else {}
    except Exception as e:
        print(f"Error loading organizations: {e}")
        return {}


# ==================== WEB ROUTES ====================

@app.route('/')
def index():
    """Root route serves home page directly (canonical URL for SEO)."""
    return render_template('home.html')

@app.route('/home')
def home():
    """Legacy /home route — 301 redirect to / for SEO consolidation."""
    return redirect('/', code=301)

@app.route('/learn-more')
def learn_more():
    return render_template('learn_more.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html',
        turnstile_site_key=os.getenv('CLOUDFLARE_TURNSTILE_SITE_KEY', ''))

@app.route('/contact/send', methods=['POST'])
def send_contact_message():
    data    = request.json
    name    = data.get('name', '').strip()
    email   = data.get('email', '').strip()
    subject = data.get('subject', '').strip()
    message = data.get('message', '').strip()
    token   = data.get('cf_turnstile_response', '')

    if not all([name, email, subject, message]):
        return jsonify({'error': 'All fields are required'}), 400
    if len(message) < 10:
        return jsonify({'error': 'Message must be at least 10 characters'}), 400

    remote_ip = request.headers.get('CF-Connecting-IP') or request.remote_addr
    if not verify_turnstile(token, remote_ip):
        return jsonify({'error': 'Security check failed. Please try again.'}), 400

    try:
        admin_email = app.config['MAIL_DEFAULT_SENDER']
        context = {'name': name, 'email': email, 'subject': subject, 'message': message}

        admin_html = load_email_template('contact_admin.html', context)
        send_html_email(
            subject=f"Contact Form: {subject}",
            recipient=admin_email,
            html_body=admin_html,
            text_body=f"New contact from {name} ({email})\nSubject: {subject}\n\n{message}"
        )

        user_html = load_email_template('contact_user.html', context)
        send_html_email(
            subject="We received your message — ShowWise",
            recipient=email,
            html_body=user_html,
            text_body=f"Hi {name},\n\nThanks for contacting ShowWise! We'll get back to you within 24 hours.\n\nShowWise Team"
        )

        return jsonify({'success': True, 'message': 'Message sent successfully!'})
    except Exception as e:
        print(f"Contact form error: {e}")
        return jsonify({'error': 'Failed to send message.'}), 500


@app.route('/quote', methods=['GET', 'POST'])
def quote():
    if request.method == 'POST':
        name         = request.form.get('name', '').strip()
        email        = request.form.get('email', '').strip()
        organization = request.form.get('organization', '').strip()
        message      = request.form.get('message', '').strip()
        token        = request.form.get('cf-turnstile-response', '')

        remote_ip = request.headers.get('CF-Connecting-IP') or request.remote_addr
        if not verify_turnstile(token, remote_ip):
            flash('Security check failed. Please try again.', 'error')
            return redirect('/quote')

        try:
            admin_email = app.config['MAIL_DEFAULT_SENDER']
            context = {'name': name, 'email': email, 'organization': organization, 'message': message}

            admin_html = load_email_template('quote_admin.html', context)
            send_html_email(
                subject=f"Quote Request — {organization}",
                recipient=admin_email,
                html_body=admin_html,
                text_body=f"New quote request from {name} ({email})\nOrg: {organization}\n\n{message}"
            )

            user_html = load_email_template('quote_user.html', context)
            send_html_email(
                subject="We received your quote request — ShowWise",
                recipient=email,
                html_body=user_html,
                text_body=f"Hi {name},\n\nThanks for your interest in ShowWise! We'll be in touch within 24 hours.\n\nShowWise Team"
            )

            flash('Your enquiry has been submitted successfully.', 'success')
        except Exception as e:
            print(f"Quote form error: {e}")
            flash('Failed to send your enquiry. Please try again later.', 'error')

        return redirect('/quote')

    return render_template('quote.html',
        turnstile_site_key=os.getenv('CLOUDFLARE_TURNSTILE_SITE_KEY', ''))


@app.route('/organizations')
def organizations_list():
    orgs = load_organizations()
    return render_template('organizations.html', organizations=orgs)

@app.route('/organizations/select/<org_slug>')
def select_organization(org_slug):
    orgs = load_organizations()
    if org_slug not in orgs:
        flash('Organization not found')
        return redirect(url_for('organizations_list'))
    return redirect(orgs[org_slug]['url'] + '/login')

@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/terms')
def terms():
    return render_template('tos.html')


# ==================== SEO ====================

@app.route('/sitemap.xml')
def sitemap():
    from datetime import datetime
    from flask import Response
    pages = [
        {'loc': '/',              'priority': '1.0', 'changefreq': 'weekly'},
        {'loc': '/learn-more',    'priority': '0.9', 'changefreq': 'monthly'},
        {'loc': '/about',         'priority': '0.8', 'changefreq': 'monthly'},
        {'loc': '/quote',         'priority': '0.8', 'changefreq': 'monthly'},
        {'loc': '/contact',       'priority': '0.7', 'changefreq': 'monthly'},
        {'loc': '/privacy-policy','priority': '0.3', 'changefreq': 'yearly'},
        {'loc': '/terms',         'priority': '0.3', 'changefreq': 'yearly'},
    ]
    today = datetime.utcnow().strftime('%Y-%m-%d')
    base = 'https://showwise.app'
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in pages:
        xml += [f'  <url>',
                f'    <loc>{base}{p["loc"]}</loc>',
                f'    <lastmod>{today}</lastmod>',
                f'    <changefreq>{p["changefreq"]}</changefreq>',
                f'    <priority>{p["priority"]}</priority>',
                f'  </url>']
    xml.append('</urlset>')
    return Response('\n'.join(xml), mimetype='application/xml')


@app.route('/robots.txt')
def robots():
    from flask import Response
    content = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /contact/send\n"
        "Disallow: /organizations/select/\n"
        "\n"
        "Sitemap: https://showwise.app/sitemap.xml\n"
    )
    return Response(content, mimetype='text/plain')


# ==================== MAIN ====================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)