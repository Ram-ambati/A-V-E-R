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
      console.log("No file selected.");
      return;
    }

    console.log("File selected for analysis:", selectedFile.name);
    processingText.classList.remove("hidden");
    resultSection.classList.add("hidden");
    resultsDiv.textContent = "";

    const formData = new FormData();
    formData.append("file", selectedFile);

    const routeMap = {
      video: "/video-analysis"
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
        console.log("Response received successfully.");
        return response.json();
      })
      .then(data => {
        console.log("Response data received:", data);

        // Check if data contains video analysis (array and non-empty)
        if (Array.isArray(data) && data.length > 0) {
          console.log("Rendering video analysis...");
          renderVideoAnalysis(data);
        } else {
          console.warn("No video analysis data found in response.");
          alert("No valid video analysis data found.");
        }

        processingText.classList.add("hidden");
        resultSection.classList.remove("hidden");
      })
      .catch((error) => {
        processingText.classList.add("hidden");
        console.error("Error during fetch request:", error);
        alert(`Error processing the file: ${error.message}`);
      });
  });

// ------------------------- RENDER VIDEO ANALYSIS ------------------------- //
function renderVideoAnalysis(videoData) {
  console.log("Starting to render video analysis...");
  const videoDiv = document.createElement('div');

  // Initialize emotion totals to calculate averages
  const emotionTotals = {
    "Angry": 0,
    "Happy": 0,
    "Neutral": 0,
    "Sad/Fear": 0,
    "Surprise/Disgust": 0
  };

  // Calculate total probabilities per emotion across all frames
  const frameCount = videoData.length;
  console.log(`Processing ${frameCount} frames...`);

  videoData.forEach(frameData => {
    console.log(`Processing frame ${frameData.frame}...`);
    // Find the dominant emotion for each frame by checking the highest probability
    const dominantEmotion = Object.entries(frameData.probabilities).reduce((prev, curr) => (prev[1] > curr[1]) ? prev : curr)[0];
    const dominantProbability = frameData.probabilities[dominantEmotion];

    emotionTotals[dominantEmotion] += dominantProbability;
    console.log(`Frame ${frameData.frame} - Dominant Emotion: ${dominantEmotion} (${(dominantProbability * 100).toFixed(2)}%)`);
  });

  // Calculate average probabilities for the dominant emotions
  const averageProbabilities = Object.fromEntries(
    Object.entries(emotionTotals).map(([emotion, total]) => [
      emotion, (total / frameCount) * 100 // Convert to percentage
    ])
  );
  console.log("Average probabilities across frames:", averageProbabilities);

  // Render HTML structure
  videoDiv.innerHTML = `
    <h3 class="font-semibold mb-2">Video Analysis</h3>
    <div class="video-analysis-container">
        <!-- Video Table -->
        <div class="video-table-container">
            <table class="w-full border-collapse" style="margin: 0 auto;">
                <thead>
                    <tr><th>Frame</th><th>Dominant Emotion</th><th>Probability</th></tr>
                </thead>
                <tbody>
                    ${videoData.map(frameData => {
                      // Find the dominant emotion for the frame
                      const dominantEmotion = Object.entries(frameData.probabilities).reduce((prev, curr) => (prev[1] > curr[1]) ? prev : curr)[0];
                      const dominantProbability = frameData.probabilities[dominantEmotion];
                      return `
                        <tr>
                            <td>${frameData.frame}</td>
                            <td>${dominantEmotion}</td>
                            <td>${(dominantProbability * 100).toFixed(2)}%</td>
                        </tr>
                      `;
                    }).join("")}
                </tbody>
            </table>
        </div>

        <!-- Video Chart -->
        <div class="video-chart-container">
            <h4 class="font-semibold mb-2">Emotion Distribution (Average Across Video)</h4>
            <canvas id="video-chart"></canvas>
        </div>
    </div>
  `;

  // Append to results container
  resultsDiv.appendChild(videoDiv);

  // Create the chart using Chart.js for the average emotion distribution
  const ctx = document.getElementById("video-chart").getContext("2d");
  const videoChart = new Chart(ctx, {
    type: 'bar', // Bar chart type
    data: {
      labels: Object.keys(averageProbabilities), // Emotion labels
      datasets: [{
        label: 'Average Emotion Probability (%)',
        data: Object.values(averageProbabilities), // Average probabilities
        backgroundColor: [
          '#FF5733', '#33FF57', '#3357FF', '#FF33A6', '#A633FF' // Different colors for each emotion
        ],
        borderColor: '#333', // Border color of bars
        borderWidth: 1
      }]
    },
    options: {
      scales: {
        y: {
          beginAtZero: true, // Start from 0 on the y-axis
          max: 100 // Set the maximum value to 100%
        }
      }
    }
  });
} // End of renderVideoAnalysis function

}); // End of DOMContentLoaded event listener