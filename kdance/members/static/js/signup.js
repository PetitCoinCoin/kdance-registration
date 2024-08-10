$(document).ready(() => {
  togglePasswords();
  postSignup();
});

function confirmPassword() {
  const pwd = $('#password');
  const pwdConfirmation = $('#password-confirmation');
  return pwdConfirmation.val() === pwd.val()
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