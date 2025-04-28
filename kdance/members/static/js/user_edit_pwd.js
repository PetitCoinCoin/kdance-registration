$(document).ready(() => {
  togglePasswords();
  updatePwd();
});

function togglePasswords() {
  ['', '-confirmation', '-old'].forEach(suffix => {
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

function confirmPassword() {
  const pwd = $('#password');
  const pwdConfirmation = $('#password-confirmation');
  return pwdConfirmation.val() === pwd.val()
}

function updatePwd() {
  $('#form-pwd').submit((event) => {
    $('.invalid-feedback').removeClass('d-inline');
    event.preventDefault();
    if (confirmPassword()) {
      $.ajax({
        url: userMePwdUrl,
        type: 'PUT',
        contentType: 'application/json',
        headers: { 'X-CSRFToken': csrftoken },
        mode: 'same-origin',
        data: JSON.stringify({
          old_password: $('#password-old').val(),
          new_password: $('#password').val(),
        }),
        dataType: 'json',
        success: () => {
          event.currentTarget.submit();
          window.location.replace('/#pwd_ok');
        },
        error: (error) => {
          if (!error.responseJSON) {
            $('#message-error-edit-pwd').removeAttr('hidden');
          }
          if (error.responseJSON.old_password) {
            $('#invalid-pwd-old').html(error.responseJSON.old_password[0]);
            $('#invalid-pwd-old').addClass('d-inline');
          }
          if (error.responseJSON.new_password) {
            $('#invalid-pwd').html(error.responseJSON.new_password[0]);
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
