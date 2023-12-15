// add hovered class to selected list item
let list = document.querySelectorAll(".navigation li");

function activeLink() {
  list.forEach((item) => {
    item.classList.remove("hovered");
  });
  this.classList.add("hovered");
}

list.forEach((item) => item.addEventListener("mouseover", activeLink));

// Menu Toggle
let toggle = document.querySelector(".toggle");
let navigation = document.querySelector(".navigation");
let main = document.querySelector(".main");

toggle.onclick = function () {
  navigation.classList.toggle("active");
  main.classList.toggle("active");
};


var modal = document.getElementById("customModal");
var btn = document.getElementById("openModalBtn");
var span = document.getElementById("closeModalBtn");

// Quando o usuário clica no botão, abre o modal
btn.onclick = function() {
  modal.style.display = "block";
}

// Quando o usuário clica no "X", fecha o modal
span.onclick = function() {
  modal.style.display = "none";
}

// Quando o usuário clica fora do modal, fecha o modal
window.onclick = function(event) {
  if (event.target == modal) {
    modal.style.display = "none";
  }
}
