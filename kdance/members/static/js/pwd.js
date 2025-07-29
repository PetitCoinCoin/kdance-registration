/************************************************************************************/
/* Copyright 2024, 2025 Andréa Marnier                                              */
/*                                                                                  */
/* This file is part of KDance registration.                                        */
/*                                                                                  */
/* KDance registration is free software: you can redistribute it and/or modify it   */
/* under the terms of the GNU Affero General Public License as published by the     */
/* Free Software Foundation, either version 3 of the License, or any later version. */
/*                                                                                  */
/* KDance registration is distributed in the hope that it will be useful, but       */
/* WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or    */
/* FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License      */
/* for more details.                                                                */
/*                                                                                  */
/* You should have received a copy of the GNU Affero General Public License along   */
/* with KDance registration. If not, see <https://www.gnu.org/licenses/>.           */
/************************************************************************************/

$(document).ready(() => {
  postNew();
  postReset();
  togglePasswords();
});

function confirmPassword() {
  const pwd = $('#password');
  const pwdConfirmation = $('#password-confirmation');
  return pwdConfirmation.val() === pwd.val()
}

function postNew() {
  $('#form-pwd-new').submit((event) => {
    event.preventDefault();
    $('.invalid-feedback').removeClass('d-inline');
    $('#message-error-new-pwd').addClass('d-none');
    $('#message-error-new-pwd').removeClass('d-inline');
    if (confirmPassword()) {
      const params = new URL(document.location.toString()).searchParams;
      const token = params.get('token');
      const data = {
        email: $('#email').val().toLowerCase(),
        password: $('#password').val(),
        token: token,
      }
      $.ajax({
        url: passwordNewUrl,
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(data),
        success: () => {
          document.getElementById('form-pwd-new').reset();
          window.location.href = '/';
        },
        error: (error) => {
          if (!error.responseJSON) {
            $('#message-error-new-pwd').removeClass('d-none');
            $('#message-error-new-pwd').addClass('d-inline');
            $('#message-error-new-pwd').html('Une erreur est survenue. Veuillez ré-essayer plus tard ou contacter K\'Dance.');
          }
          if (error.responseJSON.token) {
            $('#message-error-new-pwd').html(error.responseJSON.token[0]);
            $('#message-error-new-pwd').removeClass('d-none');
            $('#message-error-new-pwd').addClass('d-inline');
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

function postReset() {
  $('#form-pwd-reset').submit((event) => {
    event.preventDefault();
    $('.invalid-feedback').removeClass('d-inline');
    $('#message-error-reset-pwd').addClass('d-none');
    $('#message-error-reset-pwd').removeClass('d-inline');
    $.ajax({
      url: passwordResetUrl,
      type: 'POST',
      contentType: 'application/json',
      data: JSON.stringify({
        email: $('#email').val().toLowerCase(),
      }),
      success: () => {
        $('#message-ok-reset-pwd').removeClass('d-none');
        document.getElementById('form-pwd-reset').reset();
      },
      error: (error) => {
        if (!error.responseJSON) {
          $('#message-error-reset-pwd').removeClass('d-none');
          $('#message-error-reset-pwd').addClass('d-inline');
          $('#message-error-reset-pwd').html('Une erreur est survenue. Veuillez ré-essayer plus tard ou contacter K\'Dance.');
        }
        if (error.responseJSON.email) {
          $('#invalid-email').html(error.responseJSON.email[0]);
          $('#invalid-email').addClass('d-inline');
        }
      }
    });
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
