import { Component, ElementRef, inject, viewChild } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { Activity } from './core/activity';
import { Feedback } from './shared/feedback';

@Component({
  imports: [RouterOutlet, Feedback],
  selector: 'app-root',
  styleUrl: './app.css',
  templateUrl: './app.html',
})
export class App {
  readonly activity = inject(Activity);
  readonly content = viewChild.required<ElementRef<HTMLElement>>('content');

  skipToContent(event: Event) {
    event.preventDefault();
    this.content().nativeElement.focus();
  }
}
