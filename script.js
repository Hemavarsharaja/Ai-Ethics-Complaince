document.getElementById("next-btn").addEventListener("click", () => {
    document.getElementById("homepage").style.display = "none";
    document.getElementById("formpage").style.display = "block";
});

document.getElementById("upload-form").addEventListener("submit", async (e) => {
    e.preventDefault();

    const form = e.target;
    const formData = new FormData(form);
    const checks = [];

    form.querySelectorAll('input[name="checks"]:checked').forEach(cb => {
        checks.push(cb.value);
    });

    // Append checks to formData
    checks.forEach(c => formData.append("checks", c));

    // Show loader and hide results
    document.getElementById("loader").style.display = "block";
    document.getElementById("results").style.display = "none";

    try {
        const response = await fetch("http://127.0.0.1:8000/check", {
            method: "POST",
            body: formData,
        });

        const result = await response.json();

        // Display results
        document.getElementById("loader").style.display = "none";
        document.getElementById("results").style.display = "block";
        document.getElementById("score").textContent = result.compliance_score;
        document.getElementById("risk").textContent = result.risk_level;

        const suggestionsList = document.getElementById("suggestions-list");
        suggestionsList.innerHTML = "";
        result.improvement_suggestions.forEach(suggestion => {
            const li = document.createElement("li");
            li.textContent = suggestion;
            suggestionsList.appendChild(li);
        });
    } catch (error) {
        alert("Something went wrong. Please try again.");
        console.error("Error:", error);
        document.getElementById("loader").style.display = "none";
    }
});
