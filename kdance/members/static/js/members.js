$(document).ready(() => {
  getSeasons();
  updateMember();
  const seasonSelect = document.querySelector('#season-select');
  seasonSelect.addEventListener('change', () => 
    onSeasonChange(seasonSelect.value)
  );
});

function getSeasons() {
  $.ajax({
    url: seasonsUrl,
    type: 'GET',
    success: (data) => {
      data.map((season) => {
        let label = season.year;
        if (season.is_current) {
          label += ' (en cours)';
          getMembers(season.id)
        }
        $('#season-select').append($('<option>', { value: season.id, text: label, selected: season.is_current }));
      });
    },
    error: (error) => {
      // if (!error.responseJSON) {
      //     $('#message-error-signup').removeAttr('hidden');
      // }
    }
  });
}

function onSeasonChange(seasonId) {
  getMembers(seasonId);
}

function getMembers(seasonId) {
  $.ajax({
    url: membersUrl + `?season=${seasonId}`,
    type: 'GET',
    success: (data) => {
      if (document.querySelector('#members-table').className === '') {
        $('#members-table').bootstrapTable({
          search: true,
          stickyHeader: true,
          showFullscreen: true,
          showColumns: true,
          columns: [{
            field: 'id',
            title: 'ID',
            visible: false,
          }, {
            field: 'last_name',
            title: 'Nom de famille',
            searchable: true,
            sortable: true,
          }, {
            field: 'first_name',
            title: 'Prénom',
            searchable: true,
            sortable: true,
          }, {
            field: 'courses',
            title: 'Cours',
            searchable: true,
            sortable: true,
            visible: false,
          }, {
            field: 'documents.authorise_photos',
            title: 'Autorisation photos',
            searchable: true,
            sortable: true,
          }, {
            field: 'documents.authorise_emergency',
            title: 'Autorisation parentale',
            searchable: true,
            sortable: true,
          }, {
            field: 'documents.medical_document',
            title: 'Doc médical',
            searchable: true,
            sortable: true,
          }, {
            field: 'operate',
            title: 'Modifier',
            align: 'center',
            clickToSelect: false,
            formatter : function(value, row, index) {
              return `<button class="btn btn-outline-info btn-sm" memberId="${row.id}" type="button" data-bs-toggle="modal" data-bs-target="#member-modal"><i class="bi-pencil-fill"></i></button>`;
            }
          }],
          data: data.map((m) => {
            return {
              ...m,
              courses: m.courses.map((c) => c.name)
            }
          })
        });
        $('input[type=search]').attr('placeholder', 'Rechercher');
      } else {
        $('#members-table').bootstrapTable('load', data.map((m) => {
          return {
            ...m,
            courses: m.courses.map((c) => c.name)
          }
        }));
      }
    },
    error: (error) => {
      // if (!error.responseJSON) {
      //     $('#message-error-signup').removeAttr('hidden');
      // }
    }
  });
}

function getMember(memberId) {
  $.ajax({
    url: membersUrl + memberId + '/',
    type: 'GET',
    success: (data) => {
      $('#member-modal-title').html(`Mettre à jour les données de ${data.first_name} ${data.last_name}`);
      $('#doc-select').val(data.documents?.medical_document || "Manquant");
      $('#authorise-photos').prop('checked', data.documents?.authorise_photos || false);
      $('#authorise-emergency').prop('checked', data.documents?.authorise_emergency || true);
    },
    error: (error) => {
      // if (!error.responseJSON) {
      //     $('#message-error-signup').removeAttr('hidden');
      // }
    }
  });
}

function updateMember() {
  const memberModal = document.getElementById('member-modal');
  if (memberModal) {
    memberModal.addEventListener('show.bs.modal', event => {
      const button = event.relatedTarget;
      memberId = button.getAttribute('memberId');
      getMember(memberId);
      patchMember(memberId);
    });
  }
}

function patchMember(memberId) {
  $('#form-member').submit((event) => {
    $('.invalid-feedback').removeClass('d-inline');
    event.preventDefault();
    const data = {
      documents: {
        medical_document: $('#doc-select').val(),
        authorise_photos: $('#authorise-photos').is(':checked'),
        authorise_emergency: $('#authorise-emergency').is(':checked'),
      },
    }
    $.ajax({
      url: membersUrl + memberId + '/',
      type: 'PATCH',
      contentType: 'application/json',
      headers: { 'X-CSRFToken': csrftoken },
      mode: 'same-origin',
      data: JSON.stringify(data),
      dataType: 'json',
      success: () => {
        event.currentTarget.submit();
      },
      error: (error) => {
        // if (!error.responseJSON) {
        //   $('#message-error-signup').removeAttr('hidden');
        // }
      }
    });
  });
}
