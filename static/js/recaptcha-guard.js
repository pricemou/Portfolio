/* Empêche l'envoi d'un formulaire tant que la case reCAPTCHA n'est pas cochée. */
(function () {
    'use strict';

    var MESSAGE = 'Cochez « Je ne suis pas un robot » pour continuer.';

    document.addEventListener('submit', function (event) {
        var form = event.target;
        if (!form || !form.getAttribute || form.getAttribute('data-recaptcha') !== 'required') {
            return;
        }
        if (!form.querySelector('.g-recaptcha')) {
            return;
        }

        var hint = form.querySelector('.recaptcha-hint');
        var solved = window.grecaptcha && typeof grecaptcha.getResponse === 'function'
            && grecaptcha.getResponse();

        if (solved) {
            if (hint) hint.hidden = true;
            return;
        }

        event.preventDefault();
        if (hint) {
            hint.hidden = false;
            hint.textContent = MESSAGE;
        }
    }, true);
})();
