document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("upload-form");
    const loader = document.getElementById("loader");
    const results = document.getElementById("results");
    const scoreFill = document.getElementById("score-fill");
    const riskDetails = document.getElementById("risk-details");
    const suggestionsList = document.getElementById("improvement-suggestions");

    form.addEventListener("submit", async (e) => {
        e.preventDefault(); // Prevent default form submission

        loader.style.display = "block";
        results.style.display = "none";

        const formData = new FormData();
        formData.append("model_name", document.getElementById("model-name").value);
        formData.append("model_description", document.getElementById("model-description").value);
        formData.append("model_file", document.getElementById("model-file").files[0]);
        formData.append("dataset_file", document.getElementById("dataset-file").files[0]);

        // Get selected checks
        const checks = [];
        if (document.getElementById("bias-check").checked) checks.push("Bias Check");
        if (document.getElementById("transparency-audit").checked) checks.push("Transparency Audit");
        if (document.getElementById("privacy-scan").checked) checks.push("Privacy Scan");
        formData.append("checks", JSON.stringify(checks)); // Send checks as JSON

        try {
            const response = await fetch("http://127.0.0.1:8000/analyze", {
                method: "POST",
                body: formData
            });

            if (!response.ok) throw new Error("Failed to submit form.");

            const result = await response.json();
            loader.style.display = "none";
            results.style.display = "block";

            // Show the compliance score
            const score = result.score || 0;
            scoreFill.style.width = `${score}%`;
            scoreFill.innerText = `${score}%`;

            // Show risk details
            riskDetails.innerText = result.risks || "No major risks found.";

            // Show suggestions
            suggestionsList.innerHTML = "";
            if (result.suggestions && result.suggestions.length > 0) {
                result.suggestions.forEach(item => {
                    const li = document.createElement("li");
                    li.innerText = item;
                    suggestionsList.appendChild(li);
                });
            } else {
                const li = document.createElement("li");
                li.innerText = "No suggestions. Good to go!";
                suggestionsList.appendChild(li);
            }

        } catch (error) {
            loader.style.display = "none";
            alert("An error occurred: " + error.message);
        }
    });
});
