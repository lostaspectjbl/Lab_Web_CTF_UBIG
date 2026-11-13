function animateLabHeader() {
    setTimeout(function() {
        const labSolved = document.getElementById('notification-labsolved');
        if (labSolved) {
            labSolved.classList.remove('notification-labsolved-hidden');
            labSolved.classList.add('notification-labsolved');
        }
    }, 200);
}
document.addEventListener("DOMContentLoaded", animateLabHeader);
