document.addEventListener("DOMContentLoaded", function () {
    let currentIndex = 0;
    let profiles = [];

    function updateProfileDisplay() {
        const container = document.getElementById("profilesContainer");
        container.innerHTML = "";  // Clear existing profiles

        if (profiles.length === 0) {
            container.innerHTML = "<p>No matching profiles found.</p>";
            return;
        }

        const profile = profiles[currentIndex];

        const card = document.createElement("div");
        card.classList.add("profile-card", "center");

        card.innerHTML = `
            <h2>${profile.name}, ${profile.age}</h2>
            <p>${profile.bio}</p>
            <p><strong>Match Score:</strong> ${profile.match_score}</p>
            <p><strong>Collaboration Count:</strong> ${profile.collab_count}</p>
        `;

        container.appendChild(card);
    }

    function fetchProfiles() {
        fetch("/api/foryou")  // Fetch from API, not the HTML page
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    document.getElementById("profilesContainer").innerHTML = "<p>User not logged in.</p>";
                    return;
                }
                profiles = data;
                currentIndex = 0;
                updateProfileDisplay();
            })
            .catch(error => console.error("Error fetching profiles:", error));
    }

    document.getElementById("prevButton").addEventListener("click", function () {
        if (profiles.length > 0) {
            currentIndex = (currentIndex - 1 + profiles.length) % profiles.length;
            updateProfileDisplay();
        }
    });

    document.getElementById("nextButton").addEventListener("click", function () {
        if (profiles.length > 0) {
            currentIndex = (currentIndex + 1) % profiles.length;
            updateProfileDisplay();
        }
    });

    fetchProfiles();
});