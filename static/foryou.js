document.addEventListener("DOMContentLoaded", function () {
    let currentIndex = 0;
    let profiles = [];

    function updateProfileDisplay() {
        const container = document.getElementById("profilesContainer");
        container.innerHTML = "";

        if (!profiles || profiles.length === 0) {
            container.innerHTML = "<p>No matching profiles found.</p>";
            return;
        }

        const profile = profiles[currentIndex];

        console.log("Rendering profile:", profile);

        const card = document.createElement("div");
        card.classList.add("profile-card", "center");
        card.innerHTML = `
            <h2>${profile.full_name}</h2>
            <p>${profile.bio}</p>
            <p><strong>Match Score:</strong> ${profile.match_score}</p>
            <div class="action-buttons">
                <button class="like-button" data-buddy-id="${profile.user_id}">♡ Like</button>
                <button class="dislike-button" data-buddy-id="${profile.user_id}">⊘ Dislike</button>
            </div>
        `;

        card.addEventListener("click", () => showProfilePopup(profile));
        container.appendChild(card);

        attachLikeDislikeListeners();
    }

    function attachLikeDislikeListeners() {
        document.querySelectorAll(".like-button, .dislike-button").forEach(button => {
            button.addEventListener("click", (event) => {
                event.stopPropagation();
                const buddyId = event.target.dataset.buddyId;
                const liked = event.target.classList.contains("like-button");

                if (!liked) { // If Dislike button clicked
                    document.querySelector(".profile-card").classList.add("crumple-effect");

                    setTimeout(() => {
                        profiles.splice(currentIndex, 1); // Remove current profile
                        if (profiles.length === 0) {
                            currentIndex = 0;
                            document.getElementById("profilesContainer").innerHTML = "<p>No more profiles left.</p>";
                        } else {
                            updateProfileDisplay();
                        }
                    }, 700);
                } else {
                    updateBuddyRelationship(buddyId, true);
                }
            });
        });
    }

    function fetchProfiles() {
        fetch("/api/foryou")
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

function showProfilePopup(profile) {
    document.getElementById("popupName").textContent = profile.full_name;
    document.getElementById("popupBio").textContent = profile.bio;
    document.getElementById("popupStrengths").textContent = profile.strengths || "N/A";
    document.getElementById("popupWeaknesses").textContent = profile.weaknesses || "N/A";
    document.getElementById("popupMatchScore").textContent = profile.match_score;

    document.getElementById("profilePopup").style.display = "block";
}

document.getElementById("closePopup").addEventListener("click", () => {
    document.getElementById("profilePopup").style.display = "none";
});
