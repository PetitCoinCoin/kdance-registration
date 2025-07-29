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
