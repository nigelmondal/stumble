const profiles = [
    {
        name: "Apanvi Srivastava",
        bio: "An adventurous soul who loves exploring.",
        strengths: "Leadership, Creativity, Empathy",
        weaknesses: "Impatience, Perfectionism",
    },
    {
        name: "Twinkle Dhingra",
        bio: "A tech enthusiast with a love for AI.",
        strengths: "Problem-solving, Analytical skills, Adaptability",
        weaknesses: "Overthinking, Self-doubt",
    },
    {
        name: "Nigel Mondal",
        bio: "An artist who finds joy in painting and sketching.",
        strengths: "Creativity, Attention to detail, Patience",
        weaknesses: "Shyness, Reluctance to delegate",
    },
    {
        name: "Ronit Ghosh",
        bio: "A sports enthusiast who excels in teamwork.",
        strengths: "Teamwork, Leadership, Physical fitness",
        weaknesses: "Competitive nature, Impulsiveness",
    },
    {
        name: "Shrey Jain",
        bio: "A passionate coder and open-source contributor.",
        strengths: "Coding skills, Resourcefulness, Commitment",
        weaknesses: "Work-life balance, Perfectionism",
    },
];

let currentIndex = 0;

function renderProfiles() {
    const container = document.getElementById("profilesContainer");
    container.innerHTML = "";

    profiles.forEach((profile, index) => {
        const strengthsArray = profile.strengths.split(", ");
        const weaknessesArray = profile.weaknesses.split(", ");
        const matchedStrengths = strengthsArray.slice(0, 2).join(", ") || "N/A";
        const matchedWeaknesses = weaknessesArray.slice(0, 2).join(", ") || "N/A";

        const card = document.createElement("div");
        card.className = `profile-card ${index === currentIndex ? "center" : ""}`;
        card.innerHTML = `
            <h2>${profile.name}</h2>
            <p><strong>Bio:</strong> ${profile.bio}</p>
            <p><strong>Matched Strengths:</strong> ${matchedStrengths}</p>
            <p><strong>Matched Weaknesses:</strong> ${matchedWeaknesses}</p>
        `;
        card.addEventListener("click", () => openPopup(profile));
        container.appendChild(card);
    });
    updateProfilePositions();
}

function updateProfilePositions() {
    const cards = document.querySelectorAll(".profile-card");
    cards.forEach((card, index) => {
        const offset = index - currentIndex;
        card.style.transform = `translateX(${offset * 160}px) scale(${
            index === currentIndex ? 1.2 : 0.8
        })`;
        card.style.zIndex = index === currentIndex ? 2 : 1;
    });
}

function openPopup(profile) {
    document.getElementById("popupName").innerText = profile.name;
    document.getElementById("popupBio").innerText = profile.bio;
    document.getElementById("popupStrengths").innerText = profile.strengths;
    document.getElementById("popupWeaknesses").innerText = profile.weaknesses;
    document.getElementById("profilePopup").style.display = "flex";
}

function closePopup() {
    document.getElementById("profilePopup").style.display = "none";
}

function removeCurrentProfile() {
    removedProfile = profiles.splice(currentIndex, 1)[0];
    if (profiles.length === 0) {
        document.getElementById("profilesContainer").innerHTML =
            "<p>No more profiles to show!</p>";
        return;
    }
    currentIndex = currentIndex % profiles.length;
    renderProfiles();
}

function undoRemoveProfile() {
    if (removedProfile) {
        profiles.splice(currentIndex, 0, removedProfile);
        removedProfile = null;
        renderProfiles();
    }
}

document.getElementById("prevButton").addEventListener("click", () => {
    currentIndex = (currentIndex - 1 + profiles.length) % profiles.length;
    renderProfiles();
});

document.getElementById("nextButton").addEventListener("click", () => {
    currentIndex = (currentIndex + 1) % profiles.length;
    renderProfiles();
});

let likeCounter = 0;

document.getElementById("likeButton").addEventListener("click", () => {
    likeCounter++;

    if (likeCounter <= 2) {
        showNotification(`You matched with ${profiles[currentIndex].name}!🎉`);
    } else {
        showNotification(`You liked ${profiles[currentIndex].name} ✔️`);
    }

    removeCurrentProfile();
});

document.getElementById("dislikeButton").addEventListener("click", () => {
    showNotification(`You disliked ${profiles[currentIndex].name}`);
    removeCurrentProfile();
});

document.getElementById("closePopup").addEventListener("click", closePopup);

function showNotification(message) {
    const notification = document.getElementById("notification");
    notification.innerText = message;
    notification.style.display = "block";
    setTimeout(() => {
        notification.style.display = "none";
    }, 3000);
}

renderProfiles();