# Demo Pack Assets

This directory contains static assets for the AutoTuner Demo Pack system.

## Files

### `demo-pack.css`
Modern CSS stylesheet for the demo pack HTML reports. Includes:
- Responsive design for mobile and desktop
- Modern gradient header design
- Interactive tab navigation
- Metric cards with hover effects
- Status color coding (PASS/FAIL/WARNING)
- Print-friendly styles
- Loading states and animations

### `icons.svg`
SVG icon sprite containing icons used throughout the demo pack:
- `icon-brain` - Brain/AI icon for AutoTuner branding
- `icon-chart` - Chart icon for analytics
- `icon-check` - Check mark for PASS criteria
- `icon-x` - X mark for FAIL criteria
- `icon-warning` - Warning triangle
- `icon-info` - Information circle
- `icon-play` - Play button for demos
- `icon-settings` - Settings/configuration
- `icon-download` - Download action
- `icon-clock` - Time-related metrics
- `icon-target` - Target/objective metrics
- `icon-speed` - Performance/speed metrics
- `icon-memory` - Memory/caching metrics

## Usage

To use these assets in your demo pack reports:

1. **CSS**: Include the CSS file in your HTML reports:
   ```html
   <link rel="stylesheet" href="assets/demo/demo-pack.css">
   ```

2. **Icons**: Use the SVG icons with the `<use>` element:
   ```html
   <svg class="icon">
     <use href="assets/demo/icons.svg#icon-brain"></use>
   </svg>
   ```

## Customization

The CSS uses CSS custom properties (variables) defined in `:root` for easy customization:

```css
:root {
    --primary-color: #667eea;
    --secondary-color: #764ba2;
    --success-color: #28a745;
    --warning-color: #ffc107;
    --danger-color: #dc3545;
    /* ... more variables */
}
```

You can override these variables to match your brand colors.

## Browser Support

The CSS and SVG assets are designed to work in modern browsers:
- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

For older browsers, consider adding fallbacks for CSS Grid and CSS custom properties.
