const menuButton = document.querySelector(".menu_open");
const closeMenu = document.querySelector(".menu_close")
const aside = document.getElementById("aside");
const overlay = document.createElement("div"); // Create overlay dynamically



document.addEventListener("DOMContentLoaded", () => {
    // Add the overlay to the DOM
    overlay.classList.add("aside-overlay");
    document.body.appendChild(overlay);

    // Toggle aside and overlay visibility
    menuButton.addEventListener("click", () => {
        aside.classList.toggle("open"); // Toggle aside visibility
        overlay.classList.toggle("active"); // Toggle overlay visibility
    });

    // Close aside overlay is clicked
    overlay.addEventListener("click", () => {
        aside.classList.remove("open");
        overlay.classList.remove("active");
    });

    // Close aside when closeMenu button is clicked
    closeMenu.addEventListener("click", () => {
        aside.classList.remove("open");
        overlay.classList.remove("active");
    });
});