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
  getGeneralSettings();
  updateGeneralSettings();
});

function getGeneralSettings() {
  $('#message-error-site').addClass('d-none');
  $('#message-ok-site').addClass('d-none');
  $.ajax({
    url: settingsUrl,
    type: 'GET',
    success: (data) => {
      $('#allow-signup').prop('checked', data.allow_signup);
      $('#allow-new-member').prop('checked', data.allow_new_member);
      $('#pre-signup-payment-delta').val(data.pre_signup_payment_delta_days);
      $('#signup-payment-delta').val(data.signup_payment_delta_days);
    },
    error: (error) => {
      console.log(error);
      $('#message-error-site').removeClass('d-none');
    }
  });
}

function updateGeneralSettings() {
  $('#form-site').submit((event) => {
    event.preventDefault();
    $.ajax({
      url: settingsUrl,
      type: 'PUT',
      contentType: 'application/json',
      headers: { 'X-CSRFToken': csrftoken },
      mode: 'same-origin',
      data: JSON.stringify({
        allow_signup: $('#allow-signup').is(':checked'),
        allow_new_member: $('#allow-new-member').is(':checked'),
        pre_signup_payment_delta_days: $('#pre-signup-payment-delta').val(),
        signup_payment_delta_days: $('#signup-payment-delta').val(),
      }),
      dataType: 'json',
      success: (_) => {
        $('#message-ok-site').removeClass('d-none');
      },
      error: (error) => {
        console.log(error);
        $('#message-error-site').removeClass('d-none');
      }
    });
  });
}
