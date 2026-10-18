import { afterNextRender, Directive, ElementRef, inject } from '@angular/core';

@Directive({ selector: '[appFocusPanel]' })
export class FocusPanel {
  constructor() {
    const element = inject<ElementRef<HTMLElement>>(ElementRef).nativeElement;
    afterNextRender(() => {
      element.focus({ preventScroll: true });
      element.scrollIntoView?.({ block: 'nearest' });
    });
  }
}
