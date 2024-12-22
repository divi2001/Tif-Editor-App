document.addEventListener('DOMContentLoaded', function() {
    function initializeColorPickers() {
        const colorPickers = document.querySelectorAll('input[name$="-color_picker"]');
        colorPickers.forEach(picker => {
            const row = picker.closest('tr');
            const redInput = row.querySelector('input[name$="-red"]');
            const greenInput = row.querySelector('input[name$="-green"]');
            const blueInput = row.querySelector('input[name$="-blue"]');

            // Set initial color picker value
            const red = parseInt(redInput.value).toString(16).padStart(2, '0');
            const green = parseInt(greenInput.value).toString(16).padStart(2, '0');
            const blue = parseInt(blueInput.value).toString(16).padStart(2, '0');
            picker.value = `#${red}${green}${blue}`;

            // Update RGB inputs when color picker changes
            picker.addEventListener('input', function() {
                const color = this.value.substring(1); // Remove the #
                const rgb = parseInt(color, 16);
                redInput.value = (rgb >> 16) & 0xff;
                greenInput.value = (rgb >> 8) & 0xff;
                blueInput.value = rgb & 0xff;
            });

            // Update color picker when RGB inputs change
            [redInput, greenInput, blueInput].forEach(input => {
                input.addEventListener('input', function() {
                    const red = parseInt(redInput.value).toString(16).padStart(2, '0');
                    const green = parseInt(greenInput.value).toString(16).padStart(2, '0');
                    const blue = parseInt(blueInput.value).toString(16).padStart(2, '0');
                    picker.value = `#${red}${green}${blue}`;
                });
            });
        });
    }

    // Initialize color pickers on page load
    initializeColorPickers();

    // Handle dynamically added rows
    if (typeof django !== 'undefined' && django.jQuery) {
        django.jQuery(document).on('formset:added', function(event, $row, formsetName) {
            if (formsetName === 'color_set') {
                initializeColorPickers();
            }
        });
    }
});