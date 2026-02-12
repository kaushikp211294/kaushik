let pages = document.querySelectorAll('.page');
let current = 0;
const explosionSound = new Audio("music/explosion.mp3");

/* PASSWORD */
function checkPassword(){
  const pwd = document.getElementById('password').value;
  if(pwd === "2112"){
    document.getElementById('lockScreen').style.display = 'none';
    document.getElementById('content').classList.remove('hidden');
  } else {
    document.getElementById('error').innerText = "Nope 😌 Try again.";
  }
}

/* PAGE NAV */
function nextPage(){
  pages[current].classList.add('hidden');
  current++;
  pages[current].classList.remove('hidden');
}

/* GALLERY */
const galleryImages = Array.from({ length: 21 }, (_, idx) => `images/img${idx + 1}.jpg`);
let galleryIndex = 0;
const galleryImageEl = document.getElementById('galleryImage');
const galleryCounterEl = document.getElementById('galleryCounter');
const galleryContinueBtn = document.getElementById('galleryContinue');

function updateGallery(){
  if (!galleryImageEl) return;
  galleryImageEl.src = galleryImages[galleryIndex];
  galleryImageEl.alt = `Memory ${galleryIndex + 1}`;
  if (galleryCounterEl) {
    galleryCounterEl.innerText = `${galleryIndex + 1} / ${galleryImages.length}`;
  }
  if (galleryContinueBtn) {
    if (galleryIndex === galleryImages.length - 1) {
      galleryContinueBtn.classList.remove('hidden');
    } else {
      galleryContinueBtn.classList.add('hidden');
    }
  }
}

function nextImage(){
  if (galleryIndex < galleryImages.length - 1) {
    galleryIndex += 1;
    updateGallery();
  }
}

function prevImage(){
  if (galleryIndex > 0) {
    galleryIndex -= 1;
    updateGallery();
  }
}

updateGallery();

/* NO BUTTON */
const noBtn = document.getElementById('noBtn');
const yesBtn = document.getElementById('yesBtn');
const noPrompt = document.getElementById('noPrompt');
const noMessages = [
  "Are you sure??",
  "I'll cry 🥺",
  "Don't do this to me",
  "Think again, love 💞",
  "My heart will miss you",
  "Wait, please?",
  "Say yes, sunshine ☀️",
  "Give it another thought 💗"
];
let noClicks = 0;

if(noBtn){
  noBtn.addEventListener('mouseover', moveNo);
  noBtn.addEventListener('click', registerNo);
  noBtn.addEventListener('touchstart', (event) => {
    event.preventDefault();
    moveNo();
    registerNo();
  });
}

function moveNo(){
  noBtn.style.transform =
    `translate(${Math.random()*250-125}px, ${Math.random()*200-100}px)`;
}

function registerNo(){
  noClicks += 1;
  if (yesBtn) {
    const scale = 1 + noClicks * 0.1;
    yesBtn.style.transform = `scale(${scale})`;
    yesBtn.style.transition = 'transform 0.2s ease';
  }
  if (noPrompt) {
    const msg = noMessages[noClicks % noMessages.length];
    noPrompt.innerText = msg;
  }
}

/* FADE TO QUESTION */
function fadeToQuestion(){
  const fade = document.createElement('div');
  fade.style.position = 'fixed';
  fade.style.inset = '0';
  fade.style.background = '#ffd1dc';
  fade.style.opacity = '0';
  fade.style.transition = 'opacity 1.5s ease';
  fade.style.zIndex = '999';
  document.body.appendChild(fade);

  setTimeout(()=>fade.style.opacity='1',50);

  setTimeout(()=>{
    nextPage();
    fade.style.opacity='0';
    setTimeout(()=>fade.remove(),1500);
  },1500);
}

/* YES CLICK */
function yesClicked(){
  explosionSound.play();

  if (navigator.vibrate) {
    navigator.vibrate([100,60,100,300,100,60,100]);
  }

  createExplosion();
  heartbeatHearts();
  showHeartbeatMessage();
}

/* EXPLOSION */
function createExplosion(){
  const boom = document.createElement('div');
  boom.className = 'explosion';
  document.body.appendChild(boom);
  setTimeout(()=>boom.remove(),1200);
}

/* HEARTS SYNCED TO BEATS */
function heartbeatHearts(){
  const beats = [0, 500, 1200, 1900];

  beats.forEach(time=>{
    setTimeout(()=>{
      const heart = document.createElement('div');
      heart.className = 'heart';
      heart.innerHTML = '💓';
      heart.style.left = (40 + Math.random()*20) + 'vw';
      heart.style.top = '55vh';
      document.body.appendChild(heart);
      setTimeout(()=>heart.remove(),1200);
    },time);
  });
}

/* HEARTBEAT MESSAGE */
function showHeartbeatMessage(){
  const msg = document.createElement('div');
  msg.innerText = "That heartbeat was for you 💖";
  msg.style.position = 'fixed';
  msg.style.top = '50%';
  msg.style.left = '50%';
  msg.style.transform = 'translate(-50%, -50%)';
  msg.style.fontSize = '22px';
  msg.style.background = 'rgba(255,255,255,0.9)';
  msg.style.padding = '20px 30px';
  msg.style.borderRadius = '20px';
  msg.style.boxShadow = '0 10px 30px rgba(0,0,0,0.2)';
  msg.style.opacity = '0';
  msg.style.transition = 'opacity 1s ease';
  msg.style.zIndex = '1000';

  document.body.appendChild(msg);

  setTimeout(()=>msg.style.opacity='1',600);

  setTimeout(()=>{
    msg.style.opacity='0';
    setTimeout(()=>{
      msg.remove();
      nextPage();
    },1000);
  },3400);
}

/* FALLING EMOJIS */
const fallingItems = ['💖','💞','💘','🌸','🌷','🌹','🌻','🐯','😊','🥰','✨','💐'];
let fallingInterval;

function spawnFallingItem(){
  const item = document.createElement('div');
  item.className = 'falling-item';
  const sizes = ['small', 'normal', 'large'];
  const size = sizes[Math.floor(Math.random() * sizes.length)];
  if (size !== 'normal') {
    item.classList.add(size);
  }
  item.innerText = fallingItems[Math.floor(Math.random() * fallingItems.length)];
  item.style.left = `${Math.random() * 100}vw`;
  const duration = 6 + Math.random() * 6;
  item.style.animationDuration = `${duration}s`;
  document.body.appendChild(item);
  setTimeout(() => {
    item.classList.add('fade-out');
  }, (duration - 1) * 1000);
  setTimeout(() => item.remove(), duration * 1000);
}

function startFallingItems(){
  if (fallingInterval) return;
  fallingInterval = setInterval(spawnFallingItem, 450);
}

startFallingItems();
