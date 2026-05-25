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

function activatePopovers() {
  const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
  [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
}

function breadcrumbDropdownOnHover() {
  let dropdown_hover = $('.dropdown-hover');
  dropdown_hover.on('mouseover', function(){
      let menu = $(this).find('.dropdown-menu'), toggle = $(this).find('.dropdown-toggle');
      menu.addClass('show');
      toggle.addClass('show').attr('aria-expanded', true);
  });
  dropdown_hover.on('mouseout', function(){
      let menu = $(this).find('.dropdown-menu'), toggle = $(this).find('.dropdown-toggle');
      menu.removeClass('show');
      toggle.removeClass('show').attr('aria-expanded', false);
  });
}

function download(data) {
    const filename = `${data.last_name}_${data.first_name}.json`.replaceAll(' ', '-');
    const mimeType = "application/json";

    const jsonString = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonString], { type: mimeType });
    const fileUrl = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = fileUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();

    // Clean up
    document.body.removeChild(a);
    URL.revokeObjectURL(fileUrl);
}

function getSeasonsWrapper(callback, toastPrefix) {
  $.ajax({
    url: seasonsUrl,
    type: 'GET',
    success: (data) => {
        callback(data);
    },
    error: (_error) => {
      showToast('Impossible de récupérer la liste des saisons.', toastPrefix);
    }
  });
}

function onSeasonChange(seasonId, callback) {
  const refresh = window.location.protocol + "//" + window.location.host + window.location.pathname + `?season=${seasonId}`;
  window.history.pushState({ path: refresh }, '', refresh);
  callback(seasonId);
}

function showToast(text, toastPrefix, withSuffix = true) {
  const toast = bootstrap.Toast.getOrCreateInstance(document.getElementById(toastPrefix + '-toast'));
  const toastText = text + (withSuffix ? ` ${ERROR_SUFFIX}` : '');
  $(`#${toastPrefix}-body`).text(toastText);
  toast.show();
}

function showLoader() {
  $('[role=status]').attr('hidden', false);
}

function hideLoader() {
  $('[role=status]').attr('hidden', true);
}
