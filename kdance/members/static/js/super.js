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
	getSeasons();
	const seasonSelect = document.querySelector('#season-select');
	seasonSelect.addEventListener('change', () =>
		getCourses(seasonSelect.value)
	);
	const courseSelect = document.querySelector('#course-select');
	courseSelect.addEventListener('change', () =>
		getMembersPerCourse(courseSelect.value)
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
					getCourses(season.id);
				}
				$('#season-select').append($('<option>', { value: season.id, text: label, selected: season.is_current }));
			});
		},
		error: (error) => {
			showToast('Impossible de récupérer la liste des saisons.');
			console.log(error);
		}
	});
}

function getCourses(seasonId) {
	$('#course-select').empty();
	$.ajax({
		url: coursesUrl + `?season=${seasonId}`,
		type: 'GET',
		success: (data) => {
			for (let i = 0; i < data.length; i++) {
				const startHour = data[i].start_hour.split(':');
				const label = `${data[i].name}, ${WEEKDAY[data[i].weekday]} ${startHour[0]}h${startHour[1]}`;
				$('#course-select').append($('<option>', { value: data[i].id, text: label }));
			}
			getMembersPerCourse(data[0].id);
		},
		error: (error) => {
			showToast('Impossible de récupérer les cours de la saison.');
			console.log(error);
		}
	});
}

function getMembersPerCourse(courseId) {
    $.ajax({
      url: `${membersUrl}?course=${courseId}`,
      type: 'GET',
      success: (data) => {
        $('#data-table').bootstrapTable('destroy');
		buildEmergencyInfo(data, courseId);
        $('#total-count').text(data.length);
      },
      error: (error) => {
        showToast('Impossible de récupérer les informations.');
        console.log(error);
      }
    });
  }

function buildEmergencyInfo(data, courseId) {
	$('#data-table').bootstrapTable({
		...COMMON_TABLE_PARAMS,
		showExport: true,
		exportTypes: ['csv', 'xlsx', 'pdf', 'json'],
		exportOptions: {
			fileName: function () {
				const suffix = $('#menu-2-select option:selected').text();
				return `urgences_${$('#season-select option:selected').text().substring(0,9)}_${suffix}`
			}
		},
		columns: [
			{
				field: 'name',
				title: 'Adhérent',
			}, {
				field: 'name-responsible-1',
				title: 'Responsable légal 1',
			}, {
				field: 'phone-responsible-1',
				title: 'Tél 1',
			}, {
				field: 'name-responsible-2',
				title: 'Responsable légal 2',
			}, {
				field: 'phone-responsible-2',
				title: 'Tél 2',
			}, {
				field: 'name-emergency-1',
				title: 'Contact urgence 1',
			}, {
				field: 'phone-emergency-1',
				title: 'Tél urgence 1',
			}, {
				field: 'name-emergency-2',
				title: 'Contact urgence 2',
			}, {
				field: 'phone-emergency-2',
				title: 'Tél urgence 2',
			}, {
				field: 'authorise_emergency',
				title: 'Autorisation parentale',
			}],
		data: data.map(m => {
			return {
				...m,
				name: `${m.last_name} ${m.first_name}${m.cancelled_courses.map(c => c.id).indexOf(courseId) >= 0 ? ' (Annulé)' : ''}`,
				authorise_emergency: m.documents.authorise_emergency ? 'Oui': 'Non',
				...buildContactsData(m.contacts),
			}
		})
	});
}

function buildContactsData(data) {
  let contacts = {};
  Object.keys(CONTACT_MAPPING).forEach(key => {
    const subContacts = data.filter(c => c.contact_type === key);
    // Technically, we could have 3 contacts per type. But this is higly unusual
    for (i=0; i<CONTACT_NUMBER; i++) {
      contacts[`name-${key}-${i+1}`] = i < subContacts.length ? `${subContacts[i].first_name} ${subContacts[i].last_name}` : undefined;
      contacts[`phone-${key}-${i+1}`] = i < subContacts.length ? subContacts[i].phone : undefined;
      if (key === 'responsible') {
        contacts[`email-${key}-${i+1}`] = i < subContacts.length ? subContacts[i].email : undefined;
      }
    }
  });
  return contacts
}
