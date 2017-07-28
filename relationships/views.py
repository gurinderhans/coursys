import operator
from django.shortcuts import render, get_object_or_404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.http import Http404, StreamingHttpResponse
from courselib.auth import requires_role
from forms import ContactForm
from log.models import LogEntry
from models import Contact, Event, EVENT_CHOICES, EVENT_HANDLERS, EVENT_TYPES
from handlers import FileEventBase


def _get_handler_or_404(handler_slug):
    handler_slug = handler_slug.lower()
    if handler_slug in EVENT_TYPES:
        return EVENT_TYPES[handler_slug]
    else:
        raise Http404('Unknown event handler slug')


def _get_event_types():
    types = [{
        'slug': key.lower(),
        'name': Handler.name,
    } for key, Handler in EVENT_CHOICES]
    return sorted(types, key=operator.itemgetter('name'))


@requires_role('RELA')
def index(request):
    contacts = Contact.objects.filter(unit__in=request.units)
    return render(request, 'relationships/index.html', {'contacts': contacts})


@requires_role('RELA')
def view_contact(request, contact_slug):
    contact = get_object_or_404(Contact, slug=contact_slug, unit__in=request.units)
    events = Event.objects.filter(contact=contact)
    return render(request, 'relationships/view_contact.html', {'contact': contact, 'events': events})


@requires_role('RELA')
def new_contact(request):
    if request.method == 'POST':
        form = ContactForm(request, request.POST)
        if form.is_valid():
            contact = form.save()
            messages.add_message(request,
                                 messages.SUCCESS,
                                 u'Contact was created')
            l = LogEntry(userid=request.user.username,
                         description="Added contact %s" % contact,
                         related_object=contact)
            l.save()
            return HttpResponseRedirect(reverse('relationships:index'))
    else:
        form = ContactForm(request)
    return render(request, 'relationships/new_contact.html', {'form': form})


@requires_role('RELA')
def edit_contact(request, contact_slug):
    contact = get_object_or_404(Contact, slug=contact_slug, unit__in=request.units)
    if request.method == 'POST':
        form = ContactForm(request, request.POST, instance=contact)
        if form.is_valid():
            contact = form.save()
            messages.add_message(request,
                                 messages.SUCCESS,
                                 u'Contact was edited')
            l = LogEntry(userid=request.user.username,
                         description="Edited contact %s" % contact,
                         related_object=contact)
            l.save()
            return HttpResponseRedirect(reverse('relationships:index'))
    else:
        form = ContactForm(request, instance=contact)
    return render(request, 'relationships/edit_contact.html', {'form': form, 'contact': contact})


@requires_role('RELA')
def delete_contact(request, contact_slug):
    contact = get_object_or_404(Contact, slug=contact_slug, unit__in=request.units)
    if request.method == 'POST':
        contact.deleted = True
        contact.save()
        messages.add_message(request,
                             messages.SUCCESS,
                             u'Contact was deleted')
        l = LogEntry(userid=request.user.username,
                     description="Deleted contact %s" % contact,
                     related_object=contact)
        l.save()
    return HttpResponseRedirect(reverse('relationships:index'))


@requires_role('RELA')
def list_events(request, contact_slug):
    contact = get_object_or_404(Contact, slug=contact_slug, unit__in=request.units)
    events = _get_event_types()
    return render(request, 'relationships/list_events.html', {'contact': contact, 'events': events})

@requires_role('RELA')
def list_reports(request):
    events = _get_event_types()
    return render(request, 'relationships/list_reports.html', {'events': events})


@requires_role('RELA')
def add_event(request, contact_slug, handler_slug):
    contact = get_object_or_404(Contact, slug=contact_slug, unit__in=request.units)
    handler = _get_handler_or_404(handler_slug)
    if request.method == 'POST':
        form = handler.EntryForm(data=request.POST, files=request.FILES)
        # If the form has a file field, we should put the file data back in there. 
        if len(request.FILES) != 0:
            form.files = request.FILES

        if form.is_valid():
            event_handler = handler.create_for(contact=contact, form=form)
            event_handler.save()
            # In the case of our file-based handlers, what we really want to do is create the attachment that the event
            # uses for display.
            if isinstance(event_handler, FileEventBase):
                FileEventBase.add_attachment(event=event_handler.event, filedata=request.FILES)
            messages.add_message(request,
                                 messages.SUCCESS,
                                 u'Contact content was added')
            l = LogEntry(userid=request.user.username,
                         description="Added contact %s for %s" % (event_handler.name,
                                                                  event_handler.event.contact.full_name()),
                         related_object=event_handler.event)
            l.save()
            return HttpResponseRedirect(reverse('relationships:view_contact', kwargs={'contact_slug': contact_slug}))

    else:
        form = handler.EntryForm()
    return render(request, 'relationships/add_event.html', {'form': form, 'contact': contact, 'handler_slug': handler_slug})


@requires_role('RELA')
def view_event(request, contact_slug, event_slug):
    contact = get_object_or_404(Contact, slug=contact_slug, unit__in=request.units)
    event = get_object_or_404(Event, slug=event_slug, contact=contact)
    handler = event.get_handler()
    if isinstance(handler, FileEventBase):
        return _view_event_attachment(event)
    return render(request, 'relationships/view_event.html', {'contact': contact, 'event': event, 'handler': handler})


def _view_event_attachment(event):
    attachment = event.eventattachment
    filename = attachment.contents.name.rsplit('/')[-1]
    resp = StreamingHttpResponse(attachment.contents.chunks(), content_type=attachment.mediatype)
    resp['Content-Disposition'] = 'inline; filename="' + filename + '"'
    resp['Content-Length'] = attachment.contents.size
    return resp


@requires_role('RELA')
def delete_event(request, contact_slug, event_slug):
    contact = get_object_or_404(Contact, slug=contact_slug, unit__in=request.units)
    event = get_object_or_404(Event, slug=event_slug, contact=contact)
    if request.method == 'POST':
        event.deleted = True
        event.save(call_from_handler=True)
        messages.add_message(request,
                             messages.SUCCESS,
                             u'Contact content was deleted')
        l = LogEntry(userid=request.user.username,
                     description="Deleted contact %s for %s" % (event.event_type, event.contact.full_name()),
                     related_object=event)
        l.save()
        return HttpResponseRedirect(reverse('relationships:view_contact', kwargs={'contact_slug': contact_slug}))


@requires_role('RELA')
def event_report(request, handler_slug):
    handler = _get_handler_or_404(handler_slug)
    events = Event.objects.filter(event_type=handler_slug, contact__unit__in=request.units).select_related('contact')
    handler_name = handler.name
    is_text = handler.text_content

    return render(request, 'relationships/view_event_report.html', {'events': events, 'handler_name': handler_name,
                                                                    'is_text': is_text})