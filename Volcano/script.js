document.addEventListener("DOMContentLoaded", () => {
const splash = document.getElementById("splash-screen");
let dismissed = false;
let unlocking = false;

document.body.style.overflow = "hidden";

function unlockScrollAfterAnimation() {
splash.addEventListener(
"transitionend",
() => {
document.body.style.overflow = "";
unlocking = false;
},
{ once: true }
);
}

function hideSplash() {
if (dismissed || unlocking) return;
dismissed = true;
unlocking = true;
splash.classList.add("is-hidden");
unlockScrollAfterAnimation();
}

window.addEventListener(
"wheel",
(e) => {
if (!dismissed) {
e.preventDefault();
e.stopPropagation();
hideSplash();
}
},
{ passive: false }
);
window.addEventListener(
"touchmove",
(e) => {
if (!dismissed) {
e.preventDefault();
}
},
{ passive: false }
);

window.addEventListener(
"touchstart",
(e) => {
if (!dismissed) {
e.preventDefault();
hideSplash();
}
},
{ passive: false }
);

window.addEventListener("click", () => {
if (!dismissed) hideSplash();
});

window.addEventListener("keydown", () => {
if (!dismissed) hideSplash();
});
});