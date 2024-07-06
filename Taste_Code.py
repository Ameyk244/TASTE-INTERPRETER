from flask import Flask, render_template, request, send_file
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import threading

# Set the Matplotlib backend to Agg to avoid GUI-related issues
matplotlib.use('Agg')

app = Flask(__name__, template_folder="templates")

# This lock is used to ensure that Matplotlib operations are performed on the main thread.
lock = threading.Lock()


def determine_properties(wavelength):
    taste = ""
    composition = ""
    nutritional_values = {}
    health_benefits = []

    if 250 <= wavelength <= 270:
        taste = "Salty"
        composition = "Sodium chloride (salt)"
        nutritional_values = {"Sodium": "XX mg", "Calories": "XX kcal"}
        health_benefits = ["Hydration", "Electrolyte balance"]
    elif 270 <= wavelength <= 290:
        taste = "Pungent/Spicy"
        composition = "Capsaicin (in cayenne pepper), gingerol (in ginger)"
        nutritional_values = {"Capsaicin": "XX mg", "Calories": "XX kcal"}
        health_benefits = ["Metabolism boost", "Anti-inflammatory"]
    elif 300 <= wavelength <= 350:
        taste = "Sour"
        composition = "Organic acids (e.g., citric acid, oxalic acid)"
        nutritional_values = {"Vitamin C": "XX mg", "Calories": "XX kcal"}
        health_benefits = ["Antioxidant", "Digestive health"]
    elif 350 <= wavelength <= 400:
        taste = "Astringent"
        composition = "Tannins (polyphenols), catechins (in tea), ellagic acid (in pomegranate)"
        nutritional_values = {"Polyphenols": "XX mg", "Calories": "XX kcal"}
        health_benefits = ["Heart health", "Anti-inflammatory"]
    elif 400 <= wavelength <= 450:
        taste = "Bitter"
        composition = "Bitter alkaloids (e.g., taraxacin in dandelion, gentiopicroside in gentian)"
        nutritional_values = {"Bitter Compounds": "XX mg", "Calories": "XX kcal"}
        health_benefits = ["Digestive aid", "Appetite stimulation"]
    elif 500 <= wavelength <= 600:
        taste = "Sweet"
        composition = "Sugars (e.g., glucose, fructose)"
        nutritional_values = {"Sugars": "XX mg", "Calories": "XX kcal"}
        health_benefits = ["Energy source", "Mood enhancement"]
    else:
        taste = "Taste not identified within the specified range"

    return taste, composition, nutritional_values, health_benefits

def generate_plot(wavelength_range, absorbance, highest_peak_wavelength, highest_peak_absorbance):
    # Generate the Matplotlib plot and return the base64-encoded image data.
    with lock:
        plt.figure(figsize=(8, 6))
        plt.plot(wavelength_range, absorbance)
        plt.scatter([highest_peak_wavelength], [highest_peak_absorbance], color='red', marker='o', label='Highest Peak')
        plt.title("Absorbance vs. Wavelength")
        plt.xlabel("Wavelength (nm)")
        plt.ylabel("Absorbance")
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.ylim(0, 1.2)  # Set y-axis limits
        plt.legend()

        # Calculate the position for the label
        label_x = highest_peak_wavelength  # Center the label on the peak
        label_y = highest_peak_absorbance + 0.05  # Adjust the vertical position

        # Add text label for the highest peak
        plt.text(label_x, label_y, f'Highest Peak: ({highest_peak_wavelength:.2f} nm, {highest_peak_absorbance:.2f})', fontsize=10, color='red')

        # Save the plot to a BytesIO buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)

        # Encode the plot as base64 for embedding in HTML
        plot_data = base64.b64encode(buffer.read()).decode('utf-8')
        plt.show()
        plt.close()

    return plot_data

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        sample_name = request.form["sample_name"]
        input_wavelength = float(request.form["wavelength"])
        input_absorbance = float(request.form["absorbance"])

        if not (200 <= input_wavelength <= 800) or not (0 <= input_absorbance <= 1):
            return "Invalid input. Wavelength should be between 200 and 800 nm, and absorbance should be between 0 and 1."

        # Define the range for the graph based on the input wavelength
        wavelength_min = input_wavelength - 50
        wavelength_max = input_wavelength + 50

        # Generate sample data (absorbance values) within the specified range
        wavelength_range = np.linspace(wavelength_min, wavelength_max, 1000)
        peak_wavelengths = [input_wavelength - 20, input_wavelength, input_wavelength + 30] # Example: Three peaks
        peak_absorbances = [0.5, input_absorbance, 0.7] # Example: Absorbance values for the peaks

        # Create a Gaussian curve for each peak and sum them to get the final curve
        absorbance = sum([absorbance_value * np.exp(-0.01 * (wavelength_range - peak_wavelength) ** 2)
        for peak_wavelength, absorbance_value in
            zip(peak_wavelengths, peak_absorbances)])

        # Find the wavelength of the highest peak
        highest_peak_index = np.argmax(absorbance)
        highest_peak_wavelength = wavelength_range[highest_peak_index]
        highest_peak_absorbance = absorbance[highest_peak_index]

        # Generate the Matplotlib plot and get the base64-encoded image data
        plot_data = generate_plot(wavelength_range, absorbance, highest_peak_wavelength, highest_peak_absorbance)

        # Determine taste, composition, and other properties
        taste, composition, nutritional_values, health_benefits = determine_properties(input_wavelength)

        # Render an HTML template with the results
        return render_template("result.html", result_data={
            "sample_name": sample_name,
            "taste": taste,
            "composition": composition,
            "nutritional_values": nutritional_values,
            "health_benefits": health_benefits,
            "plot_data": plot_data
        })

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
