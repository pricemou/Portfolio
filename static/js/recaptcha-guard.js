/* Empêche l'envoi d'un formulaire tant que la case reCAPTCHA n'est pas cochée. */
(function () {
    'use strict';

    var MESSAGE = 'Cochez « Je ne suis pas un robot » pour continuer.';

    function client() {
        if (!window.grecaptcha) return null;
        return grecaptcha.enterprise || grecaptcha;
    }

    window.recaptchaResponse = function () {
        var api = client();
        if (!api || typeof api.getResponse !== 'function') return '';
        return api.getResponse();
    };

    window.recaptchaReset = function () {
        var api = client();
        if (api && typeof api.reset === 'function') api.reset();
    };

    document.addEventListener('submit', function (event) {
        var form = event.target;
        if (!form || !form.getAttribute || form.getAttribute('data-recaptcha') !== 'required') {
            return;
        }
        if (!form.querySelector('.g-recaptcha')) {
            return;
        }

        var hint = form.querySelector('.recaptcha-hint');
        var solved = window.recaptchaResponse();

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
