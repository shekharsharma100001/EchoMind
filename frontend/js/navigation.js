function switchPage(pageId) {
    const homeView = document.getElementById("home-view");
    const uploadView = document.getElementById("upload-view");
    const mobileMenu = document.getElementById("mobile-menu");
    const navHome = document.getElementById("nav-home");
    const navUpload = document.getElementById("nav-upload");

    if (!homeView || !uploadView) return;

    if (pageId === "home") {
        homeView.classList.remove("hidden-page");
        uploadView.classList.add("hidden-page");
    } else if (pageId === "upload") {
        uploadView.classList.remove("hidden-page");
        homeView.classList.add("hidden-page");
    }

    if (mobileMenu) {
        mobileMenu.classList.add("hidden");
    }

    if (navHome && navUpload) {
        if (pageId === "home") {
            navHome.classList.add("text-white");
            navHome.classList.remove("text-gray-400");
            navUpload.classList.remove("text-white");
            navUpload.classList.add("text-gray-400");
        } else {
            navUpload.classList.add("text-white");
            navUpload.classList.remove("text-gray-400");
            navHome.classList.remove("text-white");
            navHome.classList.add("text-gray-400");
        }
    }

    window.scrollTo({ top: 0, behavior: "smooth" });
}

function toggleMobileMenu() {
    const mobileMenu = document.getElementById("mobile-menu");
    if (mobileMenu) {
        mobileMenu.classList.toggle("hidden");
    }
}

function bindNavigation() {
    const navButtons = document.querySelectorAll("[data-page-target]");
    navButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const pageId = button.getAttribute("data-page-target");
            switchPage(pageId);
        });
    });

    const mobileMenuButton = document.getElementById("mobile-menu-button");
    if (mobileMenuButton) {
        mobileMenuButton.addEventListener("click", toggleMobileMenu);
    }
}