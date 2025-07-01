const btn = document.getElementById("cta-btn");
const btnText = btn.querySelector('.btn-text');
const cta = document.getElementById("cta");

btn.addEventListener("mouseenter", () => {
    // Animate section and button text gradient
    cta.style.backgroundPosition = "100% 50%";
    btnText.style.backgroundPosition = "100% 50%";
});

btn.addEventListener("mouseleave", () => {
    cta.style.backgroundPosition = "0% 50%";
    btnText.style.backgroundPosition = "0% 50%";
});
