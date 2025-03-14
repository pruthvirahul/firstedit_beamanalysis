from flask import Flask, render_template, request, send_file
import numpy as np
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# Function to calculate reactions at supports
def reactions(L, W1, W2, x):
    Rb = (W1 * (L - 0) + W2 * (L - x)) / L
    Ra = W1 + W2 - Rb
    return Ra, Rb

# Function to find maximum shear force and bending moment
def max_shear_bending(L, W1, W2, x):
    positions = np.linspace(0, L, 100)
    shear_forces = []
    bending_moments = []

    Ra, _ = reactions(L, W1, W2, x)

    for pos in positions:
        if pos < x:
            shear = Ra - W1
            moment = Ra * pos - W1 * pos
        elif pos == x:
            shear = Ra - W1 - W2
            moment = Ra * pos - W1 * pos - W2 * 0
        else:
            shear = Ra - W1 - W2
            moment = Ra * pos - W1 * pos - W2 * (pos - x)

        shear_forces.append(shear)
        bending_moments.append(moment)

    return positions, shear_forces, bending_moments

@app.route('/', methods=['GET', 'POST'])
def index():
    plot_url = None

    if request.method == 'POST':
        L = float(request.form['L'])
        W1 = float(request.form['W1'])
        W2 = float(request.form['W2'])
        x = float(request.form['x'])

        positions, shear_forces, bending_moments = max_shear_bending(L, W1, W2, x)

        plt.figure(figsize=(8, 5))
        plt.plot(positions, shear_forces, label="Shear Force", color='blue')
        plt.plot(positions, bending_moments, label="Bending Moment", color='red')
        plt.xlabel("Position along Beam (m)")
        plt.ylabel("Force (kN) / Moment (kN.m)")
        plt.legend()
        plt.grid(True)
        plt.title("Shear Force and Bending Moment Diagram")

        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plt.close()

    return render_template('index.html', plot_url=plot_url)

@app.route('/download')
def download():
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    return send_file(img, mimetype='image/png', as_attachment=True, download_name='beam_analysis.png')

if __name__ == '__main__':
    app.run(debug=True)
