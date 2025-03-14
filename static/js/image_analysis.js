document.addEventListener("DOMContentLoaded", () => {
  // ------------------------- CONSTANTS AND ELEMENTS ------------------------- //
  const fileInput = document.getElementById("file-input");
  const dropArea = document.getElementById("drop-area");
  const uploadForm = document.getElementById("upload-form");
  const processingTextUpload = document.getElementById("processing-text-upload");
  const processingTextCamera = document.getElementById("processing-text-camera");
  const resultSection = document.getElementById("result-section");
  const resultsDiv = document.getElementById("results");

  const startCameraBtn = document.getElementById("start-camera-btn");
  const stopCameraBtn = document.getElementById("stop-camera-btn");
  const videoWrapper = document.getElementById("video-wrapper");
  const video = document.getElementById("video");
  const captureBtn = document.getElementById("capture-btn");
  const canvas = document.getElementById("canvas");

  let selectedFile = null;
  let stream = null;
  const analysisType = document.body.dataset.analysisType;

  // ------------------------- FILE HANDLING ------------------------- //
  ["dragenter", "dragover", "dragleave", "drop"].forEach(event => {
    dropArea.addEventListener(event, e => e.preventDefault());
  });

  dropArea.addEventListener("drop", e => {
    selectedFile = e.dataTransfer.files[0];
    fileInput.files = e.dataTransfer.files;
  });

  fileInput.addEventListener("change", () => {
    selectedFile = fileInput.files[0];
  });

  // ------------------------- FORM SUBMISSION ------------------------- //
  uploadForm.addEventListener("submit", e => {
    e.preventDefault();
    if (!selectedFile) {
      alert("Please select a file.");
      return;
    }
    processingTextUpload.classList.remove("hidden"); // Show upload processing text
    processFile(selectedFile, "upload");
  });

  // ------------------------- CAMERA FUNCTIONALITY ------------------------- //
  startCameraBtn.addEventListener("click", async () => {
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: true });
      video.srcObject = stream;
      await video.play();

      videoWrapper.classList.add("show");
      startCameraBtn.classList.add("hidden");
      captureBtn.classList.remove("hidden");
      stopCameraBtn.classList.remove("hidden");
    } catch (err) {
      alert("Camera access denied or not supported.");
      console.error("Camera error:", err);
    }
  });

  captureBtn.addEventListener("click", () => {
    processingTextCamera.classList.remove("hidden"); // Show camera processing text

    const context = canvas.getContext("2d");
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(blob => {
      if (!blob) {
        alert("Failed to capture image.");
        processingTextCamera.classList.add("hidden");
        return;
      }
      selectedFile = new File([blob], "captured_image.png", { type: "image/png" });
      stopCamera();
      processFile(selectedFile, "camera");
    }, "image/png");
  });

  stopCameraBtn.addEventListener("click", () => {
    stopCamera();
  });

  function stopCamera() {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      video.srcObject = null;
    }
    videoWrapper.classList.remove("show");
    captureBtn.classList.add("hidden");
    stopCameraBtn.classList.add("hidden");
    startCameraBtn.classList.remove("hidden");
  }

  // ------------------------- PROCESS FILE ------------------------- //
  function processFile(file, source) {
    resultSection.classList.add("hidden");
    resultsDiv.textContent = "";

    const formData = new FormData();
    formData.append("file", file);

    const routeMap = { image: "/image-analysis" };
    const endpoint = routeMap[analysisType];

    if (!endpoint) {
      alert("Invalid analysis type.");
      if (source === "upload") processingTextUpload.classList.add("hidden");
      if (source === "camera") processingTextCamera.classList.add("hidden");
      return;
    }

    fetch(endpoint, { method: "POST", body: formData })
      .then(response => {
        if (!response.ok) throw new Error(`Server error: ${response.status}`);
        return response.json();
      })
      .then(data => {
        if (source === "upload") processingTextUpload.classList.add("hidden");
        if (source === "camera") processingTextCamera.classList.add("hidden");

        if (data?.emotion && data?.probabilities) {
          resultSection.classList.remove("hidden");
          renderImageAnalysis(data);
        } else {
          alert("Invalid or missing analysis data.");
        }
      })
      .catch(error => {
        if (source === "upload") processingTextUpload.classList.add("hidden");
        if (source === "camera") processingTextCamera.classList.add("hidden");
        alert(`Error: ${error.message}`);
      });
  }

  // ------------------------- RENDER IMAGE ANALYSIS ------------------------- //
  function renderImageAnalysis(imageData) {
    resultsDiv.innerHTML = `
      <h3>Image Analysis</h3>
      <p><strong>Emotion:</strong> ${imageData.emotion}</p>
      <div class="image-analysis-container">
        <div class="image-table">
          <table>
            <thead><tr><th>Emotion</th><th>Probability</th></tr></thead>
            <tbody>
              ${Object.entries(imageData.probabilities)
                .map(([emotion, prob]) => `<tr><td>${emotion}</td><td>${(prob * 100).toFixed(2)}%</td></tr>`)
                .join("")}
            </tbody>
          </table>
        </div>
        <div class="image-chart">
          <h4>Emotion Distribution (Bar Chart):</h4>
          <canvas id="image-chart"></canvas>
        </div>
      </div>
    `;

    const ctx = document.getElementById("image-chart").getContext("2d");
    new Chart(ctx, {
      type: "bar",
      data: {
        labels: Object.keys(imageData.probabilities),
        datasets: [{
          label: "Emotion Probability (%)",
          data: Object.values(imageData.probabilities).map(prob => (prob * 100).toFixed(2)),
          backgroundColor: ["#FF5733", "#33FF57", "#3357FF", "#FF33A6", "#A633FF"],
          borderColor: "#333",
          borderWidth: 1
        }]
      },
      options: {
        scales: { y: { beginAtZero: true, max: 100 } }
      }
    });
  }
});
