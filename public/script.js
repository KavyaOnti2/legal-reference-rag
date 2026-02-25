// Add smooth scroll and slight glow animation to messages
document.addEventListener("DOMContentLoaded", function() {
    const chatMessages = document.querySelectorAll(".stChatMessage");
    chatMessages.forEach((msg, index) => {
        msg.style.animationDelay = `${index * 0.1}s`;
    });
});

// Optional: Dynamic background animation
const colors = ["#0f172a", "#1e3a8a", "#111827"];
let colorIndex = 0;
setInterval(() => {
    document.body.style.background = `linear-gradient(180deg, ${colors[colorIndex]} 0%, ${colors[(colorIndex + 1) % colors.length]} 100%)`;
    colorIndex = (colorIndex + 1) % colors.length;
}, 10000);
