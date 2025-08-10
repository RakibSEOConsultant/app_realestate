from flask import Flask, render_template, request, redirect, url_for, session, Response
import pandas as pd
import plotly.express as px

app = Flask(__name__)
app.secret_key = '0b34a0b0107874e8920e4116249d76da'  # Change this to a random string

@app.route('/dashboard')
def dashboard():
    try:
        df = pd.read_csv('properties.csv')
    except Exception as e:
        return f"Error reading CSV: {e}"

    # Get filter values
    city = request.args.get('city', '')
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')
    bedrooms = request.args.get('bedrooms', '')
    property_type = request.args.get('property_type', '')

    # Apply filters
    if city:
        df = df[df['city'].str.contains(city, case=False, na=False)]
    if min_price:
        try:
            df = df[df['price'] >= float(min_price)]
        except:
            pass
    if max_price:
        try:
            df = df[df['price'] <= float(max_price)]
        except:
            pass
    if bedrooms:
        try:
            df = df[df['bedrooms'] == int(bedrooms)]
        except:
            pass
    if property_type:
        df = df[df['property_type'].str.contains(property_type, case=False, na=False)]

    # Pagination
    page = int(request.args.get('page', 1))
    per_page = 5
    start = (page - 1) * per_page
    end = start + per_page
    try:
        table_html = df.iloc[start:end].to_html(classes='table table-striped', index=False, escape=False, 
            formatters={'id': lambda x: f'<a href="/property/{x}">{x}</a>'})
    except Exception as e:
        return f"Error creating table: {e}"

    total_pages = (len(df) + per_page - 1) // per_page

    # Chart
    chart_div = ""
    if not df.empty:
        try:
            fig = px.bar(df.groupby('city')['price'].mean().reset_index(), x='city', y='price', title='Average Price by City')
            chart_div = fig.to_html(full_html=False)
        except Exception as e:
            chart_div = f"<p>Error creating chart: {e}</p>"

    return render_template(
        'dashboard.html',
        table=table_html,
        city=city,
        min_price=min_price,
        max_price=max_price,
        bedrooms=bedrooms,
        property_type=property_type,
        chart_div=chart_div,
        page=page,
        total_pages=total_pages
    )

@app.route('/property/<int:property_id>', methods=['GET'])
def property_detail(property_id):
    df = pd.read_csv('properties.csv')
    prop = df[df['id'] == property_id].iloc[0]
    return render_template('property_detail.html', prop=prop)

@app.route('/lead/<int:property_id>', methods=['POST'])
def lead(property_id):
    name = request.form['name']
    email = request.form['email']
    with open('leads.txt', 'a') as f:
        f.write(f"{property_id},{name},{email}\n")
    return "Thank you! An agent will contact you soon."

@app.route('/export')
def export():
    df = pd.read_csv('properties.csv')
    # Apply filters as in dashboard
    city = request.args.get('city', '')
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')
    bedrooms = request.args.get('bedrooms', '')
    property_type = request.args.get('property_type', '')

    if city:
        df = df[df['city'].str.contains(city, case=False, na=False)]
    if min_price:
        df = df[df['price'] >= float(min_price)]
    if max_price:
        df = df[df['price'] <= float(max_price)]
    if bedrooms:
        df = df[df['bedrooms'] == int(bedrooms)]
    if property_type:
        df = df[df['property_type'].str.contains(property_type, case=False, na=False)]

    csv = df.to_csv(index=False)
    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=filtered_properties.csv"}
    )

@app.route('/agent-login', methods=['GET', 'POST'])
def agent_login():
    if request.method == 'POST':
        if request.form['password'] == 'yourpassword':  # Change this password!
            session['agent'] = True
            return redirect(url_for('agent_dashboard'))
    return render_template('agent_login.html')

@app.route('/agent-dashboard')
def agent_dashboard():
    if not session.get('agent'):
        return redirect(url_for('agent_login'))
    leads = []
    try:
        with open('leads.txt', 'r') as f:
            for line in f:
                leads.append(line.strip().split(','))
    except FileNotFoundError:
        leads = []
    return render_template('agent_dashboard.html', leads=leads)

@app.route('/')
def home():
    return redirect(url_for('dashboard'))

