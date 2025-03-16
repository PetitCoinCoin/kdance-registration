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
        const errorMessage = 'Une erreur est survenue, impossible de supprimer le compte pour le moment.';
        showToast(errorMessage);
        console.log(error);
      }
    });
  });
}

function showToast(text) {
  const toast = bootstrap.Toast.getOrCreateInstance(document.getElementById('user-delete-error-toast'));
  $('#user-delete-error-body').text(`${text} ${ERROR_SUFFIX}`);
  toast.show();
}
