document.addEventListener("DOMContentLoaded", () => {
  // ------------------------- CONSTANTS AND ELEMENTS ------------------------- //
  const fileInput = document.getElementById("file-input");
  const dropArea = document.getElementById("drop-area");
  const uploadForm = document.getElementById("upload-form");
  const processingText = document.getElementById("processing-text");
  const resultSection = document.getElementById("result-section");
  const resultsDiv = document.getElementById("results");

  let selectedFile = null;
  const analysisType = document.body.dataset.analysisType; // Get analysis type from HTML attribute

  // ------------------------- FILE HANDLING ------------------------- //
  // 🛡️ Prevent default drag behaviors
  ["dragenter", "dragover", "dragleave", "drop"].forEach(event => {
    dropArea.addEventListener(event, e => e.preventDefault());
  });

  // 📂 Handle dropped file
  dropArea.addEventListener("drop", e => {
    selectedFile = e.dataTransfer.files[0];
    fileInput.files = e.dataTransfer.files;
    console.log(`Dropped file: ${selectedFile.name}`);
  });

  // 📝 Handle file selection
  fileInput.addEventListener("change", () => {
    selectedFile = fileInput.files[0];
    console.log(`File selected: ${selectedFile.name}`);
  });

  // ------------------------- FORM SUBMISSION ------------------------- //
  // 🚀 Handle form submission
  uploadForm.addEventListener("submit", (e) => {
    e.preventDefault();

    if (!selectedFile) {
      alert("Please select a file.");
      return;
    }

    processingText.classList.remove("hidden");
    resultSection.classList.add("hidden");
    resultsDiv.textContent = "";

    const formData = new FormData();
    formData.append("file", selectedFile);

    const routeMap = {
      image: "/image-analysis" // Adjust endpoint for image analysis
    };

    const endpoint = routeMap[analysisType];

    if (!endpoint) {
      console.error(`Invalid analysis type: ${analysisType}`);
      alert("Invalid analysis type selected.");
      return;
    }

    console.log(`Sending request to ${endpoint} with file: ${selectedFile.name}`);

    // ------------------------- FETCH REQUEST ------------------------- //
    fetch(endpoint, { method: "POST", body: formData })
      .then(response => {
        if (!response.ok) {
          throw new Error(`Server error: ${response.status} ${response.statusText}`);
        }
        return response.json();
      })
      .then(data => {
        console.log("Response data received:", data); // Log the entire response
        if (data && data.emotion && data.probabilities) {
          processingText.classList.add("hidden");
          resultSection.classList.remove("hidden");
          renderImageAnalysis(data);  // Pass the `data` directly
        } else {
          console.error("Invalid image data:", data);
          alert("Error: Invalid or missing image analysis data.");
        }
      })
      .catch((error) => {
        processingText.classList.add("hidden");
        console.error("Error during fetch request:", error);
        alert(`Error processing the file: ${error.message}`);
      });
  });

  // ------------------------- RENDER IMAGE ANALYSIS ------------------------- //
  function renderImageAnalysis(imageData) {
    if (!imageData || !imageData.emotion || !imageData.probabilities) {
      console.error("Invalid image data:", imageData);
      alert("Error: Invalid or missing image analysis data.");
      return;
    }

    const imageDiv = document.createElement('div');
    imageDiv.innerHTML = `
      <h3 class="font-semibold mb-2">Image Analysis</h3>
      <p><strong>Emotion:</strong> ${imageData.emotion}</p>
      <h4>Probabilities:</h4>
  
      <!-- Container for table and chart -->
      <div class="image-analysis-container">
        <!-- Image Table -->
        <div class="image-table">
          <table class="w-full border-collapse" style="margin: 0 auto;">
            <thead>
              <tr><th>Emotion</th><th>Probability</th></tr>
            </thead>
            <tbody>
              ${Object.entries(imageData.probabilities)
                .map(([emotion, prob]) =>
                  `<tr><td>${emotion}</td><td>${(prob * 100).toFixed(2)}%</td></tr>`)
                .join("")}
            </tbody>
          </table>
        </div>
        <!-- Image Chart -->
        <div class="image-chart">
          <h4>Emotion Distribution (Bar Chart):</h4>
          <canvas id="image-chart"></canvas>
        </div>
      </div>
    `;
    resultsDiv.appendChild(imageDiv);

    // Chart.js setup to create the bar chart for image probabilities
    const ctx = document.getElementById("image-chart").getContext("2d");
    const imageChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: Object.keys(imageData.probabilities),
        datasets: [{
          label: 'Emotion Probability (%)',
          data: Object.values(imageData.probabilities).map(prob => (prob * 100).toFixed(2)),
          backgroundColor: [
            '#FF5733', '#33FF57', '#3357FF', '#FF33A6', '#A633FF'
          ],
          borderColor: '#333',
          borderWidth: 1
        }]
      },
      options: {
        scales: {
          y: {
            beginAtZero: true,
            max: 100
          }
        }
      }
    });
  }
});
