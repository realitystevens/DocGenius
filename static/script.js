console.log("Hello from the client side!");

const pdfForm = document.getElementById("pdfForm");
const submitBtn = document.getElementById("submitBtn");
const fileInput = document.getElementById("pdfFile");
const questionInput = document.getElementById("question");
const extractedText = document.getElementById("extractedText");
const answer = document.getElementById("answer");



submitBtn.addEventListener("click", function(e) {
    e.preventDefault();

    if (fileInput && question) {
        const formData = new FormData();
        formData.append("file", fileInput.files[0]);
        formData.append("question", questionInput.value);

        fetch("/api/v1", {
            method: "POST",
            body: formData
        }).then(response => response.json())
        .then(data => {
            console.log(data);
            extractedText.textContent = data.extractedPDFText;
            answer.textContent = data.answer || "No answer available.";
        })
        .catch(error => {
            console.error(error);
            extractedText.textContent = "";
            answer.textContent = "An error occurred. Please try again.";
        });
    } else {
        console.log("Either the file or the question is missing. Please provide both fields and try again.");
        extractedText.textContent = "";
        answer.textContent = "Either the file or the question is missing. Please provide both fields and try again.";
    }
});
