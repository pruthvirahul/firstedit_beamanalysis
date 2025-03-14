from flask import Flask, render_template, request, send_file, session
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
from fpdf import FPDF
import os

app = Flask(__name__)
app.secret_key = 'beam_analysis_secret'

# Function to calculate reactions at supports
def reactions(L, W1, W2, x):
    Rb = (W1 * (L - 0) + W2 * (L - x)) / L
    Ra = W1 + W2 - Rb
    return Ra, Rb

# Function to calculate shear force and bending moment

def max_shear_bending(L, W1, W2, x):
    positions = np.linspace(0, L, 100)
    shear_forces = []
    bending_moments = []

    Ra, Rb = reactions(L, W1, W2, x)

    for pos in positions:
        if pos < x:
            shear = Ra - W1
            moment = Ra * pos - W1 * pos
        else:
            shear = Ra - W1 - W2
            moment = Ra * pos - W1 * pos - W2 * (pos - x)

        shear_forces.append(shear)
        bending_moments.append(moment)

    SF_max = max(shear_forces, key=abs)
    BM_max = max(bending_moments)
    return SF_max, BM_max

@app.route('/', methods=['GET', 'POST'])
def index():
    plot_url = None
    results = {}

    if request.method == 'POST':
        L = float(request.form['L'])
        W1 = float(request.form['W1'])
        W2 = float(request.form['W2'])
        x = float(request.form['x'])

        Ra, Rb = reactions(L, W1, W2, x)
        SF_max, BM_max = max_shear_bending(L, W1, W2, x)

        # Plotting
        positions = np.linspace(0, L, 100)
        plt.plot(positions, [Ra - W1 if pos < x else Ra - W1 - W2 for pos in positions], label="Shear Force")
        plt.plot(positions, [Ra * pos - W1 * pos if pos < x else Ra * pos - W1 * pos - W2 * (pos - x) for pos in positions], label="Bending Moment")
        plt.legend()
        plt.grid(True)

        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plt.close()

        # Save the image locally for PDF download
        with open("static/beam_plot.png", "wb") as f:
            f.write(img.getvalue())

        # Store results in session
        session['results'] = {
            'Ra': round(Ra, 2),
            'Rb': round(Rb, 2),
            'BM_01': 0,
            'SF_01': Ra - W1,
            'SF_max': round(SF_max, 2),
            'BM_max': round(BM_max, 2)
        }

    return render_template('index.html', plot_url=plot_url, results=session.get('results'))

@app.route('/download')
def download():
    results = session.get('results', {})

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Beam Analysis Report", ln=True, align='C')
    pdf.ln(10)

    pdf.cell(200, 10, txt=f"Maximum Reaction at A: {results['Ra']} kN", ln=True)
    pdf.cell(200, 10, txt=f"Maximum Reaction at B: {results['Rb']} kN", ln=True)
    pdf.cell(200, 10, txt=f"Bending Moment BM_01: {results['BM_01']} kN.m", ln=True)
    pdf.cell(200, 10, txt=f"Shear Force SF_01: {results['SF_01']} kN", ln=True)
    pdf.cell(200, 10, txt=f"Maximum Shear Force SF_max: {results['SF_max']} kN", ln=True)
    pdf.cell(200, 10, txt=f"Maximum Bending Moment BM_max: {results['BM_max']} kN.m", ln=True)

    pdf.ln(10)
    pdf.image("static/beam_plot.png", x=10, y=None, w=180)

    pdf_file = "beam_analysis_report.pdf"
    pdf.output(pdf_file)

    return send_file(pdf_file, as_attachment=True)

if __name__ != '__main__':
    gunicorn_app = app

