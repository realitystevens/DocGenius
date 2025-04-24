document.addEventListener("DOMContentLoaded", () => {
    const modalOverlay = document.getElementById("modalOverlay");
    const loginModal = document.getElementById("loginModal");

    // Display the modal after the DOM is fully loaded
    modalOverlay.style.display = "flex";

    // Handle form submission
    const loginForm = document.getElementById("loginForm");
    loginForm.addEventListener("submit", (e) => {
        e.preventDefault(); // Prevent form from refreshing the page
        const username = document.getElementById("username").value;
        const password = document.getElementById("password").value;

        // Perform login logic here (e.g., send credentials to the server)
        console.log("Username:", username);
        console.log("Password:", password);

        // Hide the modal after successful login
        modalOverlay.style.display = "none";
    });
});