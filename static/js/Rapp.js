/*==================================================
                NEBULA PORTFOLIO
                app.js
==================================================*/
console.log("🔥 Rapp.js loaded");
/*==============================
TYPING EFFECT
==============================*/

const headlinesData = document.getElementById("headlines-data");
const typing = document.querySelector(".typing");

if (headlinesData && typing) {

    const words = JSON.parse(headlinesData.textContent);

    let wordIndex = 0;
    let letterIndex = 0;
    let deleting = false;

    function typeEffect() {

        const currentWord = words[wordIndex];

        if (!deleting) {

            typing.textContent = currentWord.substring(
                0,
                letterIndex++
            );

            if (letterIndex > currentWord.length) {

                deleting = true;

                setTimeout(typeEffect, 1600);

                return;

            }

        } else {

            typing.textContent = currentWord.substring(
                0,
                letterIndex--
            );

            if (letterIndex < 0) {

                deleting = false;

                wordIndex++;

                if (wordIndex >= words.length) {

                    wordIndex = 0;

                }

            }

        }

        setTimeout(
            typeEffect,
            deleting ? 45 : 90
        );

    }

    typeEffect();

}



/*==============================
SCROLL PROGRESS
==============================*/

const progress = document.querySelector(".progress-bar");

window.addEventListener("scroll", () => {

    if (!progress) return;

    const total = document.documentElement.scrollHeight - window.innerHeight;

    const percent = (window.scrollY / total) * 100;

    progress.style.width = percent + "%";

});



/*==============================
BACKGROUND ORBIT ON SCROLL
==============================*/

const bgLayer = document.querySelector(".background");

window.addEventListener("scroll", () => {

    if (!bgLayer) return;

    const total = document.documentElement.scrollHeight - window.innerHeight;

    const percent = window.scrollY / total;

    const angle = (-45 + percent * 360) * Math.PI / 180;

    const radius = 65;

    const x1 = 50 + Math.cos(angle) * radius;
    const y1 = 50 + Math.sin(angle) * radius;

    const x2 = 50 - Math.cos(angle) * radius;
    const y2 = 50 - Math.sin(angle) * radius;

    bgLayer.style.setProperty("--x1", x1 + "%");
    bgLayer.style.setProperty("--y1", y1 + "%");
    bgLayer.style.setProperty("--x2", x2 + "%");
    bgLayer.style.setProperty("--y2", y2 + "%");

});

/*==============================
HEADER SCROLL
==============================*/

const header = document.querySelector(".header");

window.addEventListener("scroll", () => {

    if (!header) return;

    if (window.scrollY > 40) {

        header.classList.add("scrolled");

    } else {

        header.classList.remove("scrolled");

    }

});


/*==============================
REVEAL ANIMATION
==============================*/

const reveals = document.querySelectorAll(

    ".about-card,.skill-box,.project-card,.blog-card,.contact,.section-title,.hero-stats"

);

function revealSections() {

    reveals.forEach(item => {

        const top = item.getBoundingClientRect().top;

        if (top < window.innerHeight - 120) {

            item.classList.add("reveal");
            item.classList.add("active");

        }

    });

}

window.addEventListener("scroll", revealSections);

revealSections();


/*==============================
MOBILE MENU
==============================*/

const menuBtn = document.querySelector(".menu-btn");
const navbar = document.querySelector(".navbar");

if (menuBtn && navbar) {

    menuBtn.addEventListener("click", () => {

        navbar.classList.toggle("active");
        menuBtn.classList.toggle("active");

    });

    document.querySelectorAll(".navbar a").forEach(link => {

        link.addEventListener("click", () => {

            navbar.classList.remove("active");
            menuBtn.classList.remove("active");

        });

    });

}


// =========================
// Smooth Scroll
// =========================

document.querySelectorAll('a[href*="#"]').forEach((anchor) => {
    anchor.addEventListener("click", function (e) {
        const url = new URL(this.href, window.location.href);

        // فقط لینک‌هایی که داخل همین صفحه هستند
        if (url.pathname !== window.location.pathname || !url.hash) {
            return;
        }

        const target = document.getElementById(url.hash.slice(1));

        if (!target) {
            return;
        }

        e.preventDefault();

        target.scrollIntoView({
            behavior: "smooth",
            block: "start",
        });

        history.replaceState(null, "", url.hash);
    });
});


// =========================
// Active Navigation
// =========================

const sections = document.querySelectorAll("main section");
const navLinks = document.querySelectorAll(".navbar a[href*='#']");

function updateActiveNav() {

    const isHomePage = window.location.pathname === "/";

    if (!isHomePage) {
        navLinks.forEach((link) => {
            link.classList.remove("active");
        });

        return;
    }

    let current = "home";

    sections.forEach((section) => {
        const top = section.offsetTop - 140;

        if (window.scrollY >= top) {
            current = section.id;
        }
    });

    navLinks.forEach((link) => {
        const url = new URL(link.href, window.location.href);
        const targetHash = url.hash;

        link.classList.toggle(
            "active",
            targetHash === `#${current}`
        );
    });
}

window.addEventListener("scroll", updateActiveNav);
window.addEventListener("load", updateActiveNav);

updateActiveNav();


/*==============================
PARALLAX ORBS
==============================*/

const orb1 = document.querySelector(".orb-1");
const orb2 = document.querySelector(".orb-2");

document.addEventListener("mousemove", e => {

    const x = (e.clientX / window.innerWidth - 0.5) * 20;
    const y = (e.clientY / window.innerHeight - 0.5) * 20;

if (orb1) {

    orb1.style.setProperty(
        "--mouse-x",
        `${x}px`
    );

    orb1.style.setProperty(
        "--mouse-y",
        `${y}px`
    );

}

if (orb2) {

    orb2.style.setProperty(
        "--mouse-x",
        `${-x}px`
    );

    orb2.style.setProperty(
        "--mouse-y",
        `${-y}px`
    );

}

});

/* =========================
   BLOG CATEGORY DROPDOWN
   ========================= */

const customSelect = document.querySelector("[data-select]");

if (customSelect) {
    const trigger = customSelect.querySelector(".custom-select-trigger");

    const closeSelect = () => {
        customSelect.classList.remove("open");
        trigger.setAttribute("aria-expanded", "false");
    };

    trigger.addEventListener("click", () => {
        const isOpen = customSelect.classList.toggle("open");

        trigger.setAttribute(
            "aria-expanded",
            String(isOpen)
        );
    });

    document.addEventListener("click", (event) => {
        if (!customSelect.contains(event.target)) {
            closeSelect();
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeSelect();
        }
    });
}

// =========================
// Logo Navigation
// =========================

const logo = document.querySelector("[data-logo]");

if (logo) {
    logo.addEventListener("click", function (e) {
        e.preventDefault();

        window.scrollTo({
            top: 0,
            behavior: "smooth",
        });
    });
}