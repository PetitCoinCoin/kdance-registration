$(document).ready(() => {
  activatePopovers();
  togglePasswords();
  getGeneralSettings();
  postSignup();
});

function confirmPassword() {
  const pwd = $('#password');
  const pwdConfirmation = $('#password-confirmation');
  return pwdConfirmation.val() === pwd.val()
}

function activatePopovers() {
  const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
  [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
}

function getGeneralSettings() {
  $('#message-error-signup').addClass('d-none');
  $.ajax({
    url: settingsUrl,
    type: 'GET',
    success: (data) => {
      if (! data.allow_signup) {
        $('#btn-signup').prop('disabled', true);
        $(':input').prop('disabled', true);
        $('#message-error-signup').text('Les inscriptions sur le site ne sont pas autorisées pour le moment. Merci de revenir plus tard ou de contacter K\'Dance directement.');
        $('#message-error-signup').removeClass('d-none');
      }
    },
    error: (error) => {
      console.log(error);
      $('#message-error-signup').removeClass('d-none');
    }
  });
}

function postSignup() {
  $('#form-signup').submit((event) => {
    event.preventDefault();
    $('.invalid-feedback').removeClass('d-inline');
    $('#message-error-signup').addClass('d-none');
    if (confirmPassword()) {
      const data = {
        username: $('#email').val().toLowerCase(),
        first_name: $('#firstname').val(),
        last_name: $('#lastname').val(),
        phone: $('#phone').val(),
        email: $('#email').val().toLowerCase(),
        address: $('#address').val(),
        postal_code: $('#postal-code').val(),
        city: $('#city').val(),
        password: $('#password').val(),
      }
      $.ajax({
        url: usersUrl,
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(data),
        dataType: 'json',
        success: () => {
          document.getElementById('form-signup').reset();
          window.location.href = '/';
        },
        error: (error) => {
          if (!error.responseJSON) {
            $('#message-error-signup').removeClass('d-none');
          }
          if (error.responseJSON.username) {
            $('#invalid-username').html(error.responseJSON.username[0]);
            $('#invalid-username').addClass('d-inline');
          }
          if (error.responseJSON.phone) {
            $('#invalid-phone').html(error.responseJSON.phone[0]);
            $('#invalid-phone').addClass('d-inline');
          }
          if (error.responseJSON.address) {
            $('#invalid-address').html(error.responseJSON.address[0]);
            $('#invalid-address').addClass('d-inline');
          }
          if (error.responseJSON.postal_code) {
            $('#invalid-postal-code').html(error.responseJSON.postal_code[0]);
            $('#invalid-postal-code').addClass('d-inline');
          }
          if (error.responseJSON.city) {
            $('#invalid-city').html(error.responseJSON.city[0]);
            $('#invalid-city').addClass('d-inline');
          }
          if (error.responseJSON.email) {
            $('#invalid-email').html(error.responseJSON.email[0]);
            $('#invalid-email').addClass('d-inline');
          }
          if (error.responseJSON.password) {
            $('#invalid-pwd').html(error.responseJSON.password[0]);
            $('#invalid-pwd').addClass('d-inline');
          }
        }
      });
    } else {
      $('#invalid-pwd-confirmation').addClass('d-inline');
      return
    }
  });
}

function togglePasswords() {
  ['', '-confirmation'].forEach(suffix => {
    const togglePassword = document.querySelector(`#toggle-password${suffix}`);
    const password = document.querySelector(`#password${suffix}`);
    togglePassword.addEventListener('click', function () {
      const type = password.getAttribute('type') === 'password' ? 'text' : 'password';
      password.setAttribute('type', type);
      this.classList.toggle('bi-eye');
      this.classList.toggle('bi-eye-slash');
    });
  });
}
