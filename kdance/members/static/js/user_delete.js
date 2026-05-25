/************************************************************************************/
/* Copyright 2024 - present, Andréa Marnier                                              */
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
  deleteUser();
});

function deleteUser() {
  $(document).on("click", "#user-delete-btn", function () {
    $.ajax({
      url: userMeUrl,
      type: 'DELETE',
      headers: { 'X-CSRFToken': csrftoken },
      mode: 'same-origin',
      success: () => {
        window.location.replace('/');
      },
      error: (error) => {
        const errorMessage = error.status === 403 ? "Vous ne pouvez pas supprimer votre compte pour le moment, car il y a toujours des adhérents pour la saison en cours (même si vous avez annulé les cours). Veuillez attendre la fin de la saison." : 'Une erreur est survenue, impossible de supprimer le compte pour le moment. ' + ERROR_SUFFIX;
        const options =  error.status === 403 ? { delay: 10000 } : undefined
        showToast(errorMessage, options);
      }
    });
  });
}

function showToast(text, options = {}) {
  const toast = bootstrap.Toast.getOrCreateInstance(document.getElementById('user-delete-error-toast'), options);
  $('#user-delete-error-body').text(text);
  toast.show();
}
