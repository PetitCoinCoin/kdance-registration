$(document).ready(() => {
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
        username: $('#username').val(),
        first_name: $('#firstname').val(),
        last_name: $('#lastname').val(),
        phone: $('#phone').val(),
        email: $('#email').val(),
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
          $('#message-ok-signup').removeClass('d-none');
          $('#message-ok-signup').delay(10000).fadeOut(1000);
          document.getElementById('form-signup').reset();
        },
        error: (error) => {
          if (!error.responseJSON) {
            $('#message-error-signup').removeAttr('hidden');
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
