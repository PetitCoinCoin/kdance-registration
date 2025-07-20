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
