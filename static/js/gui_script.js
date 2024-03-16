// entity checkbox is disabled if the element has been selected in the mapping area
function updateCheckboxes(selectElement) {
    var selectedEntities = selectElement.value + '_entity';
    var selectedData = selectElement.value + '_data';

    var checkboxes = document.querySelectorAll('.checkbox');
    var allSelects = document.querySelectorAll('.form-select');

    var selectCheck = Array.from(allSelects, element => element[element.selectedIndex].value);

    console.log(selectCheck);

    checkboxes.forEach(checkbox => {
        if (checkbox.name.includes('entity')) {
            var name = checkbox.name.replace('_entity', '');
            checkbox.disabled = selectCheck.includes(name);
        }
        if (checkbox.name.includes('data')) {
            var name = checkbox.name.replace('_data', '');
            //checkbox.checked = selectCheck.includes(name);
            checkbox.disabled = selectCheck.includes(name);
        }

        if (checkbox.disabled){
            checkbox.checked = false
        }

    });
}

/**
 * Check the property value if the entity is checked
 */
document.addEventListener("DOMContentLoaded", function() {
    var entityCheckboxes = document.querySelectorAll(".form-check-input[type='checkbox'][id$='_entity']");

    entityCheckboxes.forEach(function(entityCheckbox) {
        entityCheckbox.addEventListener("change", function() {
            var entityId = this.id;
            var dataCheckboxId = entityId.replace("_entity", "_data");
            var dataCheckbox = document.getElementById(dataCheckboxId);
            
            if (this.checked) {
                dataCheckbox.checked = true;
            }
        });
    });
});

