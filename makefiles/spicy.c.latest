/* -*- Mode: C; c-basic-offset: 4; indent-tabs-mode: nil -*- */
/*
   Copyright (C) 2010-2011 Red Hat, Inc.

   This library is free software; you can redistribute it and/or
   modify it under the terms of the GNU Lesser General Public
   License as published by the Free Software Foundation; either
   version 2.1 of the License, or (at your option) any later version.

   This library is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   Lesser General Public License for more details.

   You should have received a copy of the GNU Lesser General Public
   License along with this library; if not, see <http://www.gnu.org/licenses/>.
*/
#include "config.h"
#include <glib.h>
#include <glib/gi18n.h>
#include <locale.h>
#include <libintl.h>
#include <string.h>

#ifdef _WIN32
#include <windows.h>
#endif

#include <sys/stat.h>
#ifdef HAVE_TERMIOS_H
#include <termios.h>
#endif

#include "spice-widget.h"
#include "spice-gtk-session.h"
#include "spice-audio.h"
#include "spice-common.h"
#include "spice-cmdline.h"
#include "spice-option.h"
#include "usb-device-widget.h"

#ifndef LOCALEDIR
#define LOCALEDIR "/usr/share/locale"
#endif

#ifndef GETTEXT_PACKAGE
#define GETTEXT_PACKAGE "spice-gtk"
#endif

static void init_i18n(void)
{
    setlocale(LC_ALL, "");

#ifdef _WIN32
    char exe_dir[MAX_PATH];
    char *last_slash;

    GetModuleFileNameA(NULL, exe_dir, MAX_PATH);

    last_slash = strrchr(exe_dir, '\\');
    if (last_slash != NULL)
        *last_slash = '\0';

    strcat(exe_dir, "\\locale");

    bindtextdomain(GETTEXT_PACKAGE, exe_dir);
#else
    bindtextdomain(GETTEXT_PACKAGE, LOCALEDIR);
#endif

    bind_textdomain_codeset(GETTEXT_PACKAGE, "UTF-8");
    textdomain(GETTEXT_PACKAGE);
}

#include "spicy-connect.h"
#include <gst/gst.h>

#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>

typedef struct spice_connection spice_connection;

enum {
    STATE_SCROLL_LOCK,
    STATE_CAPS_LOCK,
    STATE_NUM_LOCK,
    STATE_MAX,
};

#define SPICE_TYPE_WINDOW                  (spice_window_get_type ())
#define SPICE_WINDOW(obj)                  (G_TYPE_CHECK_INSTANCE_CAST ((obj), SPICE_TYPE_WINDOW, SpiceWindow))
#define SPICE_IS_WINDOW(obj)               (G_TYPE_CHECK_INSTANCE_TYPE ((obj), SPICE_TYPE_WINDOW))
#define SPICE_WINDOW_CLASS(klass)          (G_TYPE_CHECK_CLASS_CAST ((klass), SPICE_TYPE_WINDOW, SpiceWindowClass))
#define SPICE_IS_WINDOW_CLASS(klass)       (G_TYPE_CHECK_CLASS_TYPE ((klass), SPICE_TYPE_WINDOW))
#define SPICE_WINDOW_GET_CLASS(obj)        (G_TYPE_INSTANCE_GET_CLASS ((obj), SPICE_TYPE_WINDOW, SpiceWindowClass))

typedef struct _SpiceWindow SpiceWindow;
typedef struct _SpiceWindowClass SpiceWindowClass;

struct _SpiceWindow {
    GObject          object;
    spice_connection *conn;
    gint             id;
    gint             monitor_id;
    GtkWidget        *toplevel, *spice;
    GtkWidget        *menubar, *toolbar;
    GtkWidget        *ritem, *rmenu;
    GtkWidget        *statusbar, *status, *st[STATE_MAX];
    GtkActionGroup   *ag;
    GtkUIManager     *ui;
    bool             fullscreen;
    bool             mouse_grabbed;
    SpiceChannel     *display_channel;
    /* Fullscreen overlay (auto-hide top control bar) */
    GtkWidget        *overlay;
    GtkWidget        *top_revealer;
    GtkWidget        *top_bar;
    GtkWidget        *hotzone;
    gint             hotzone_width;
    guint            hide_timeout;
    gboolean         overlay_hover;
    gboolean         hover_hotzone;
    gboolean         hover_bar;
    gboolean         destroying;
#ifdef G_OS_WIN32
    gint             win_x;
    gint             win_y;
#endif
    gboolean         enable_accels_save;
    gboolean         enable_mnemonics_save;
};

struct _SpiceWindowClass
{
  GObjectClass parent_class;
};

static GType spice_window_get_type(void);

G_DEFINE_TYPE (SpiceWindow, spice_window, G_TYPE_OBJECT)

#define CHANNELID_MAX 4
#define MONITORID_MAX 4


// FIXME: turn this into an object, get rid of fixed wins array, use
// signals to replace the various callback that iterate over wins array
struct spice_connection {
    SpiceSession     *session;
    SpiceGtkSession  *gtk_session;
    SpiceMainChannel *main;
    SpiceWindow     *wins[CHANNELID_MAX * MONITORID_MAX];
    SpiceAudio       *audio;
    const char       *mouse_state;
    const char       *agent_state;
    gboolean         agent_connected;
    int              disconnecting;

    /* key: SpiceFileTransferTask, value: TransferTaskWidgets */
    GHashTable *transfers;
    GtkWidget *transfer_dialog;
};

static spice_connection *connection_new(void);
static void connection_connect(spice_connection *conn);
static void connection_disconnect(spice_connection *conn);
static void connection_destroy(SpiceSession *session,
                               spice_connection *conn);
static void usb_connect_failed(GObject               *object,
                               SpiceUsbDevice        *device,
                               GError                *error,
                               gpointer               data);
static gboolean is_gtk_session_property(const gchar *property);
static void del_window(spice_connection *conn, SpiceWindow *win);

/* options */
static gboolean fullscreen = false;
static gboolean version = false;
static char *spicy_title = NULL;
#ifdef USE_USBREDIR
static char *usb_policy = NULL; /* legacy: raw:/block:/allow: */
static char *usb_redirection = NULL; /* enabled|disabled */
static char *usb_existing_devices = NULL; /* deny|manual|connect */
static char *usb_new_devices = NULL; /* deny|manual|connect */
static char *usb_default_action = NULL; /* deny|allow|connect */
static GPtrArray *usb_policy_rules = NULL; /* gchar* CLI rules */
static gboolean usb_policy_cli_active = FALSE;
#endif
/* globals */
static GMainLoop     *mainloop = NULL;
static int           connections = 0;
static GKeyFile      *keyfile = NULL;
static SpicePortChannel*stdin_port = NULL;

/* ------------------------------------------------------------------ */
static GLogWriterOutput
spicy_log_writer(GLogLevelFlags log_level,
                 const GLogField *fields,
                 gsize n_fields,
                 gpointer user_data)
{
    const gchar *domain = NULL;
    const gchar *message = NULL;
    gsize i;

    (void)user_data;

    for (i = 0; i < n_fields; i++) {
        if (g_strcmp0(fields[i].key, "GLIB_DOMAIN") == 0)
            domain = (const gchar *)fields[i].value;
        else if (g_strcmp0(fields[i].key, "MESSAGE") == 0)
            message = (const gchar *)fields[i].value;
    }

    if (message) {
        if (strstr(message, "gtk_menu_item_set_submenu: assertion 'GTK_IS_MENU_ITEM (menu_item)' failed"))
            return G_LOG_WRITER_HANDLED;
        if (domain && g_strcmp0(domain, "Gdk") == 0 && strstr(message, "cursor image size"))
            return G_LOG_WRITER_HANDLED;
    }

    return g_log_writer_default(log_level, fields, n_fields, user_data);
}

/* ------------------------------------------------------------------ */

static int ask_user(GtkWidget *parent, char *title, char *message,
                    char *dest, int dlen, int hide)
{
    GtkWidget *dialog, *area, *label, *entry;
    const char *txt;
    int retval;

    /* Create the widgets */
    dialog = gtk_dialog_new_with_buttons(title,
                                         parent ? GTK_WINDOW(parent) : NULL,
                                         GTK_DIALOG_DESTROY_WITH_PARENT,
                                         "_OK",
                                         GTK_RESPONSE_ACCEPT,
                                         "_Cancel",
                                         GTK_RESPONSE_REJECT,
                                         NULL);
    gtk_dialog_set_default_response(GTK_DIALOG(dialog), GTK_RESPONSE_ACCEPT);
    area = gtk_dialog_get_content_area(GTK_DIALOG(dialog));

    label = gtk_label_new(message);
    gtk_misc_set_alignment(GTK_MISC(label), 0, 0.5);
    gtk_box_pack_start(GTK_BOX(area), label, FALSE, FALSE, 5);

    entry = gtk_entry_new();
    gtk_entry_set_text(GTK_ENTRY(entry), dest);
    gtk_entry_set_activates_default(GTK_ENTRY(entry), TRUE);
    if (hide)
        gtk_entry_set_visibility(GTK_ENTRY(entry), FALSE);
    gtk_box_pack_start(GTK_BOX(area), entry, FALSE, FALSE, 5);

    /* show and wait for response */
    gtk_widget_show_all(dialog);
    switch (gtk_dialog_run(GTK_DIALOG(dialog))) {
    case GTK_RESPONSE_ACCEPT:
        txt = gtk_entry_get_text(GTK_ENTRY(entry));
        snprintf(dest, dlen, "%s", txt);
        retval = 0;
        break;
    default:
        retval = -1;
        break;
    }
    gtk_widget_destroy(dialog);
    return retval;
}

//static void update_status_window(SpiceWindow *win)
//{
//    GString *status;
//
//    if (win == NULL)
//        return;
//
//    status = g_string_new(NULL);
//    g_string_printf(status, "mouse: %6s, agent: %3s",
//                    win->conn->mouse_state,
//                    win->conn->agent_state);
//
//    if (win->mouse_grabbed) {
//        SpiceGrabSequence *sequence = spice_display_get_grab_keys(SPICE_DISPLAY(win->spice));
//        gchar *seq = spice_grab_sequence_as_string(sequence);
//        g_string_append_printf(status, "\tUse %s to ungrab mouse", seq);
//        g_free(seq);
//    }
//
//    gtk_label_set_text(GTK_LABEL(win->status), status->str);
//    g_string_free(status, TRUE);
//}

static void update_status_window(SpiceWindow *win)
{
    GString *status;

    if (win == NULL)
        return;

    status = g_string_new(NULL);

    /* <<< ADD gettext HERE >>> */
    g_string_printf(status,
                    _("mouse: %6s, agent: %3s"),
                    win->conn->mouse_state,
                    win->conn->agent_state);

    if (win->mouse_grabbed) {
        SpiceGrabSequence *sequence = spice_display_get_grab_keys(SPICE_DISPLAY(win->spice));
        gchar *seq = spice_grab_sequence_as_string(sequence);

        /* <<< ALSO TRANSLATABLE >>> */
        g_string_append_printf(status,
                               _("\tUse %s to ungrab mouse"),
                               seq);

        g_free(seq);
    }

    gtk_label_set_text(GTK_LABEL(win->status), status->str);
    g_string_free(status, TRUE);
}

static void update_status(struct spice_connection *conn)
{
    int i;

    for (i = 0; i < SPICE_N_ELEMENTS(conn->wins); i++) {
        if (conn->wins[i] == NULL)
            continue;
        update_status_window(conn->wins[i]);
    }
}

static const char *spice_edit_properties[] = {
    "CopyToGuest",
    "PasteFromGuest",
};

static void update_edit_menu_window(SpiceWindow *win)
{
    int i;
    GtkAction *toggle;

    if (win == NULL) {
        return;
    }

    /* Make "CopyToGuest" and "PasteFromGuest" insensitive if spice
     * agent is not connected */
    for (i = 0; i < G_N_ELEMENTS(spice_edit_properties); i++) {
        toggle = gtk_action_group_get_action(win->ag, spice_edit_properties[i]);
        if (toggle) {
            gtk_action_set_sensitive(toggle, win->conn->agent_connected);
        }
    }
}

static void update_edit_menu(struct spice_connection *conn)
{
    int i;

    for (i = 0; i < SPICE_N_ELEMENTS(conn->wins); i++) {
        if (conn->wins[i]) {
            update_edit_menu_window(conn->wins[i]);
        }
    }
}

static void menu_cb_connect(GtkAction *action, void *data)
{
    struct spice_connection *conn;

    conn = connection_new();
    connection_connect(conn);
}

static void menu_cb_close(GtkAction *action, void *data)
{
    SpiceWindow *win = data;

    connection_disconnect(win->conn);
}

static void menu_cb_copy(GtkAction *action, void *data)
{
    SpiceWindow *win = data;

    spice_gtk_session_copy_to_guest(win->conn->gtk_session);
}

static void menu_cb_paste(GtkAction *action, void *data)
{
    SpiceWindow *win = data;

    spice_gtk_session_paste_from_guest(win->conn->gtk_session);
}

static void window_set_fullscreen(SpiceWindow *win, gboolean fs)
{
    if (fs) {
#ifdef G_OS_WIN32
        gtk_window_get_position(GTK_WINDOW(win->toplevel), &win->win_x, &win->win_y);
#endif
        gtk_window_fullscreen(GTK_WINDOW(win->toplevel));
    } else {
        gtk_window_unfullscreen(GTK_WINDOW(win->toplevel));
#ifdef G_OS_WIN32
        gtk_window_move(GTK_WINDOW(win->toplevel), win->win_x, win->win_y);
#endif
    }
}

static void menu_cb_fullscreen(GtkAction *action, void *data)
{
    SpiceWindow *win = data;

    window_set_fullscreen(win, !win->fullscreen);
}

#ifdef USE_SMARTCARD
static void enable_smartcard_actions(SpiceWindow *win, VReader *reader,
                                     gboolean can_insert, gboolean can_remove)
{
    GtkAction *action;

    if ((reader != NULL) && (!spice_smartcard_reader_is_software((SpiceSmartcardReader*)reader)))
    {
        /* Having menu actions to insert/remove smartcards only makes sense
         * for software smartcard readers, don't do anything when the event
         * we received was for a "real" smartcard reader.
         */
        return;
    }
    action = gtk_action_group_get_action(win->ag, "InsertSmartcard");
    g_return_if_fail(action != NULL);
    gtk_action_set_sensitive(action, can_insert);
    action = gtk_action_group_get_action(win->ag, "RemoveSmartcard");
    g_return_if_fail(action != NULL);
    gtk_action_set_sensitive(action, can_remove);
}


static void reader_added_cb(SpiceSmartcardManager *manager, VReader *reader,
                            gpointer user_data)
{
    enable_smartcard_actions(user_data, reader, TRUE, FALSE);
}

static void reader_removed_cb(SpiceSmartcardManager *manager, VReader *reader,
                              gpointer user_data)
{
    enable_smartcard_actions(user_data, reader, FALSE, FALSE);
}

static void card_inserted_cb(SpiceSmartcardManager *manager, VReader *reader,
                             gpointer user_data)
{
    enable_smartcard_actions(user_data, reader, FALSE, TRUE);
}

static void card_removed_cb(SpiceSmartcardManager *manager, VReader *reader,
                            gpointer user_data)
{
    enable_smartcard_actions(user_data, reader, TRUE, FALSE);
}

static void menu_cb_insert_smartcard(GtkAction *action, void *data)
{
    spice_smartcard_manager_insert_card(spice_smartcard_manager_get());
}

static void menu_cb_remove_smartcard(GtkAction *action, void *data)
{
    spice_smartcard_manager_remove_card(spice_smartcard_manager_get());
}
#endif

static void menu_cb_mouse_mode(GtkAction *action, void *data)
{
    SpiceWindow *win = data;
    SpiceMainChannel *cmain = win->conn->main;
    int mode;

    g_object_get(cmain, "mouse-mode", &mode, NULL);
    if (mode == SPICE_MOUSE_MODE_CLIENT)
        mode = SPICE_MOUSE_MODE_SERVER;
    else
        mode = SPICE_MOUSE_MODE_CLIENT;

    spice_main_channel_request_mouse_mode(cmain, mode);
}

#ifdef USE_USBREDIR
static void remove_cb(GtkContainer *container, GtkWidget *widget, void *data)
{
    gtk_window_resize(GTK_WINDOW(data), 1, 1);
}

static void menu_cb_select_usb_devices(GtkAction *action, void *data)
{
    GtkWidget *dialog, *area, *usb_device_widget;
    SpiceWindow *win = data;

    /* Create the widgets */
    dialog = gtk_dialog_new_with_buttons(
                    "Select USB devices for redirection",
                    GTK_WINDOW(win->toplevel),
                    GTK_DIALOG_MODAL | GTK_DIALOG_DESTROY_WITH_PARENT,
                    "_Close", GTK_RESPONSE_ACCEPT,
                    NULL);
    gtk_dialog_set_default_response(GTK_DIALOG(dialog), GTK_RESPONSE_ACCEPT);
    gtk_container_set_border_width(GTK_CONTAINER(dialog), 12);
    gtk_box_set_spacing(GTK_BOX(gtk_bin_get_child(GTK_BIN(dialog))), 12);

    area = gtk_dialog_get_content_area(GTK_DIALOG(dialog));

    usb_device_widget = spice_usb_device_widget_new(win->conn->session,
                                                    NULL); /* default format */
    g_signal_connect(usb_device_widget, "connect-failed",
                     G_CALLBACK(usb_connect_failed), NULL);
    gtk_box_pack_start(GTK_BOX(area), usb_device_widget, TRUE, TRUE, 0);

    /* This shrinks the dialog when USB devices are unplugged */
    g_signal_connect(usb_device_widget, "remove",
                     G_CALLBACK(remove_cb), dialog);

    /* show and run */
    gtk_widget_show_all(dialog);
    gtk_dialog_run(GTK_DIALOG(dialog));
    gtk_widget_destroy(dialog);
}
#endif

static void menu_cb_bool_prop(GtkToggleAction *action, gpointer data)
{
    SpiceWindow *win = data;
    gboolean state = gtk_toggle_action_get_active(action);
    const char *name;
    gpointer object;

    name = gtk_action_get_name(GTK_ACTION(action));
    SPICE_DEBUG("%s: %s = %s", __FUNCTION__, name, state ? "yes" : "no");

#ifdef USE_USBREDIR
    if (usb_policy_cli_active && g_str_equal(name, "auto-usbredir")) {
        gboolean forced_state = FALSE;

        g_object_get(win->conn->gtk_session, "auto-usbredir", &forced_state, NULL);
        if (state != forced_state) {
            gtk_toggle_action_set_active(action, forced_state);
        }
        return;
    }
#endif

    g_key_file_set_boolean(keyfile, "general", name, state);

    if (is_gtk_session_property(name)) {
        object = win->conn->gtk_session;
    } else {
        object = win->spice;
    }
    g_object_set(object, name, state, NULL);
}

static void menu_cb_conn_bool_prop_changed(GObject    *gobject,
                                           GParamSpec *pspec,
                                           gpointer    user_data)
{
    SpiceWindow *win = user_data;
    const gchar *property = g_param_spec_get_name(pspec);
    GtkAction *toggle;
    gboolean state;

    toggle = gtk_action_group_get_action(win->ag, property);
    g_object_get(win->conn->gtk_session, property, &state, NULL);
    gtk_toggle_action_set_active(GTK_TOGGLE_ACTION(toggle), state);
}

static void menu_cb_toolbar(GtkToggleAction *action, gpointer data)
{
    SpiceWindow *win = data;
    gboolean state = gtk_toggle_action_get_active(action);

    gtk_widget_set_visible(win->toolbar, state);
    g_key_file_set_boolean(keyfile, "ui", "toolbar", state);
}

static void menu_cb_statusbar(GtkToggleAction *action, gpointer data)
{
    SpiceWindow *win = data;
    gboolean state = gtk_toggle_action_get_active(action);

    gtk_widget_set_visible(win->statusbar, state);
    g_key_file_set_boolean(keyfile, "ui", "statusbar", state);
}

static void menu_cb_about(GtkAction *action, void *data)
{
    char *comments = "gtk test client app for the\n"
        "spice remote desktop protocol";
    static const char *copyright = "(c) 2010 Red Hat";
    static const char *website = "http://www.spice-space.org";
    static const char *authors[] = { "Gerd Hoffmann <kraxel@redhat.com>",
                               "Marc-André Lureau <marcandre.lureau@redhat.com>",
                               NULL };
    SpiceWindow *win = data;

    gtk_show_about_dialog(GTK_WINDOW(win->toplevel),
                          "authors",         authors,
                          "comments",        comments,
                          "copyright",       copyright,
                          "logo-icon-name",  "help-about",
                          "website",         website,
                          "version",         PACKAGE_VERSION,
                          "license",         "LGPLv2.1",
                          NULL);
}

static gboolean delete_cb(GtkWidget *widget, GdkEvent *event, gpointer data)
{
    SpiceWindow *win = data;

    if (win->monitor_id == 0)
        connection_disconnect(win->conn);
    else
        del_window(win->conn, win);

    return true;
}


/* Fullscreen overlay helpers */
static void fs_overlay_cancel_hide(SpiceWindow *win);
static void fs_overlay_build(SpiceWindow *win);
static gboolean fs_overlay_hotzone_enter_cb(GtkWidget *widget, GdkEventCrossing *event, gpointer user_data);
static gboolean fs_overlay_hotzone_leave_cb(GtkWidget *widget, GdkEventCrossing *event, gpointer user_data);
static gboolean window_state_cb(GtkWidget *widget G_GNUC_UNUSED,
                                GdkEventWindowState *event,
                                gpointer data)
{
    SpiceWindow *win = data;

    if (!win || win->destroying)
        return FALSE;

    if (event->changed_mask & GDK_WINDOW_STATE_FULLSCREEN) {
        win->fullscreen = (event->new_window_state & GDK_WINDOW_STATE_FULLSCREEN) != 0;

        if (win->fullscreen) {
            if (win->menubar && GTK_IS_WIDGET(win->menubar))
                gtk_widget_hide(win->menubar);
            if (win->toolbar && GTK_IS_WIDGET(win->toolbar))
                gtk_widget_hide(win->toolbar);
            if (win->statusbar && GTK_IS_WIDGET(win->statusbar))
                gtk_widget_hide(win->statusbar);

            /* Ensure overlay starts hidden and is shown only on hover */
            win->overlay_hover = FALSE;
            fs_overlay_cancel_hide(win);
            if (win->spice && GTK_IS_WIDGET(win->spice))
                gtk_widget_grab_focus(win->spice);
            /* Keep overlay widgets active in fullscreen:
             * - revealer child stays hidden until hover
             * - hotzone strip remains visible to hint where to hover
             */
            if (win->top_revealer && GTK_IS_WIDGET(win->top_revealer)) {
                gtk_revealer_set_reveal_child(GTK_REVEALER(win->top_revealer), FALSE);
                gtk_widget_show(win->top_revealer);
            }
            if (win->hotzone && GTK_IS_WIDGET(win->hotzone))
                gtk_widget_show(win->hotzone);
            fs_overlay_cancel_hide(win);
            win->hover_hotzone = FALSE;
            win->hover_bar = FALSE;
            win->overlay_hover = FALSE;

        } else {
            gboolean state;
            GtkAction *toggle;

            fs_overlay_cancel_hide(win);
            win->overlay_hover = FALSE;
            if (win->top_revealer && GTK_IS_WIDGET(win->top_revealer)) {
                gtk_revealer_set_reveal_child(GTK_REVEALER(win->top_revealer), FALSE);
                gtk_widget_hide(win->top_revealer);
            }
            if (win->hotzone && GTK_IS_WIDGET(win->hotzone))
                gtk_widget_hide(win->hotzone);

            if (win->menubar && GTK_IS_WIDGET(win->menubar))
                gtk_widget_show(win->menubar);

            toggle = gtk_action_group_get_action(win->ag, "Toolbar");
            state = gtk_toggle_action_get_active(GTK_TOGGLE_ACTION(toggle));
            if (win->toolbar && GTK_IS_WIDGET(win->toolbar))
                gtk_widget_set_visible(win->toolbar, state);

            toggle = gtk_action_group_get_action(win->ag, "Statusbar");
            state = gtk_toggle_action_get_active(GTK_TOGGLE_ACTION(toggle));
            if (win->statusbar && GTK_IS_WIDGET(win->statusbar))
                gtk_widget_set_visible(win->statusbar, state);
        }
    }

    return TRUE;
}



/* ------------------------------------------------------------------ */
/* Fullscreen top overlay bar (auto show on mouse near top, auto hide) */

static void fs_overlay_cancel_hide(SpiceWindow *win)
{
    if (win->hide_timeout) {
        g_source_remove(win->hide_timeout);
        win->hide_timeout = 0;
    }
}

static gboolean fs_overlay_hide_cb(gpointer user_data)
{
    SpiceWindow *win = user_data;
    if (!win)
        return G_SOURCE_REMOVE;

    win->hide_timeout = 0;

    if (win->destroying || !win->fullscreen)
        return G_SOURCE_REMOVE;

    /* Do not hide while hovering the bar */
    if (win->overlay_hover)
        return G_SOURCE_REMOVE;

    if (win->top_revealer && GTK_IS_WIDGET(win->top_revealer))
        gtk_revealer_set_reveal_child(GTK_REVEALER(win->top_revealer), FALSE);

    return G_SOURCE_REMOVE;
}

static void fs_overlay_schedule_hide(SpiceWindow *win)
{
    fs_overlay_cancel_hide(win);
    win->hide_timeout = g_timeout_add(1000, fs_overlay_hide_cb, win);
}

static void fs_overlay_show(SpiceWindow *win)
{
    if (!win || win->destroying || !win->fullscreen)
        return;

    if (win->top_revealer && GTK_IS_WIDGET(win->top_revealer))
        gtk_revealer_set_reveal_child(GTK_REVEALER(win->top_revealer), TRUE);

    if (!win->overlay_hover)
        fs_overlay_schedule_hide(win);
    else
        fs_overlay_cancel_hide(win);
}

static gboolean fs_overlay_bar_enter_cb(GtkWidget *widget G_GNUC_UNUSED,
                                        GdkEventCrossing *event G_GNUC_UNUSED,
                                        gpointer user_data)
{
    SpiceWindow *win = user_data;

    if (!win || win->destroying)
        return FALSE;

    win->hover_bar = TRUE;
    win->overlay_hover = TRUE;
    fs_overlay_cancel_hide(win);
    return FALSE;
}

static gboolean fs_overlay_bar_leave_cb(GtkWidget *widget G_GNUC_UNUSED,
                                        GdkEventCrossing *event G_GNUC_UNUSED,
                                        gpointer user_data)
{
    SpiceWindow *win = user_data;

    if (!win || win->destroying)
        return FALSE;

    win->hover_bar = FALSE;
    win->overlay_hover = win->hover_hotzone;

    if (win->fullscreen && !win->overlay_hover)
        fs_overlay_schedule_hide(win);

    return FALSE;
}


static gboolean fs_overlay_hotzone_enter_cb(GtkWidget *widget G_GNUC_UNUSED,
                                            GdkEventCrossing *event G_GNUC_UNUSED,
                                            gpointer user_data)
{
    SpiceWindow *win = user_data;
    if (!win || !win->fullscreen)
        return GDK_EVENT_PROPAGATE;

    win->hover_hotzone = TRUE;
    win->overlay_hover = TRUE;
    fs_overlay_cancel_hide(win);
    fs_overlay_show(win);
    return GDK_EVENT_PROPAGATE;
}

static gboolean fs_overlay_hotzone_leave_cb(GtkWidget *widget G_GNUC_UNUSED,
                                            GdkEventCrossing *event G_GNUC_UNUSED,
                                            gpointer user_data)
{
    SpiceWindow *win = user_data;
    if (!win)
        return GDK_EVENT_PROPAGATE;

    win->hover_hotzone = FALSE;
    win->overlay_hover = win->hover_bar;
    if (!win->overlay_hover)
        fs_overlay_schedule_hide(win);

    return GDK_EVENT_PROPAGATE;
}

static void fs_overlay_top_bar_size_allocate(GtkWidget *widget G_GNUC_UNUSED,
                                            GdkRectangle *allocation,
                                            gpointer user_data)
{
    SpiceWindow *win = user_data;
    if (!win || !win->hotzone || !allocation)
        return;

    /*
     * Restrict trigger area to the *controls* width, not the full-width
     * revealer/eventbox allocation. The visible controls live inside the
     * child box of top_bar.
     */
    GtkWidget *child = NULL;
    GtkAllocation child_alloc;
    memset(&child_alloc, 0, sizeof(child_alloc));

    if (win->top_bar && GTK_IS_BIN(win->top_bar))
        child = gtk_bin_get_child(GTK_BIN(win->top_bar));

    if (child && gtk_widget_get_visible(child)) {
        gtk_widget_get_allocation(child, &child_alloc);
        if (child_alloc.width > 0)
            win->hotzone_width = child_alloc.width;
    } else if (allocation->width > 0) {
        win->hotzone_width = allocation->width;
    }

    if (win->hotzone_width <= 0)
        win->hotzone_width = 420;
    gtk_widget_set_size_request(win->hotzone, win->hotzone_width, 4);
}

static void fs_overlay_btn_exit_fullscreen_clicked(GtkButton *btn G_GNUC_UNUSED, gpointer user_data)
{
    SpiceWindow *win = user_data;
    if (!win || win->destroying)
        return;

    gtk_window_unfullscreen(GTK_WINDOW(win->toplevel));
}

static void fs_overlay_btn_disconnect_clicked(GtkButton *btn G_GNUC_UNUSED, gpointer user_data)
{
    SpiceWindow *win = user_data;
    if (!win || win->destroying)
        return;

    if (win->monitor_id == 0)
        connection_disconnect(win->conn);
    else
        del_window(win->conn, win);
}

static void fs_overlay_css_init(void)
{
    static gboolean inited = FALSE;
    if (inited)
        return;
    inited = TRUE;

    GtkCssProvider *provider = gtk_css_provider_new();
    /* User explicitly requested red coloring for these buttons */
    const gchar *css =
        ".fs-overlay-danger {"
        "  background-image: none;"
        "  background-color: #cc0000;"
        "  color: #ffffff;"
        "}"
        ".fs-overlay-danger:hover {"
        "  background-color: #a00000;"
        "}"
        ".fs-overlay-hotzone {"
        "  background-color: rgba(255,255,255,0.10);"
        "}";
    gtk_css_provider_load_from_data(provider, css, -1, NULL);
    gtk_style_context_add_provider_for_screen(gdk_screen_get_default(),
                                              GTK_STYLE_PROVIDER(provider),
                                              GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);
    g_object_unref(provider);
}

static gchar *strip_mnemonic_underscore(const gchar *label)
{
    if (!label)
        return NULL;
    gchar *dup = g_strdup(label);
    gchar *src = dup;
    gchar *dst = dup;
    while (*src) {
        if (*src != '_')
            *dst++ = *src;
        src++;
    }
    *dst = '\0';
    return dup;
}

typedef struct {
    GtkWidget *menu; /* GtkMenu */
} FsOverlayMenuBtn;

static void fs_overlay_menu_button_clicked(GtkButton *btn, gpointer user_data)
{
    FsOverlayMenuBtn *d = user_data;
    if (!d || !d->menu || !GTK_IS_MENU(d->menu))
        return;

#if GTK_CHECK_VERSION(3, 22, 0)
    gtk_menu_popup_at_widget(GTK_MENU(d->menu), GTK_WIDGET(btn),
                             GDK_GRAVITY_SOUTH, GDK_GRAVITY_NORTH, NULL);
#else
    gtk_menu_popup(GTK_MENU(d->menu), NULL, NULL, NULL, NULL, 0, gtk_get_current_event_time());
#endif
}

static GtkWidget *fs_overlay_menu_button_new(SpiceWindow *win,
                                             const gchar *ui_path,
                                             const gchar *action_name,
                                             const gchar *fallback_label)
{
    GtkWidget *mi;
    GtkWidget *submenu;
    GtkAction *act;
    gchar *label = NULL;

    mi = gtk_ui_manager_get_widget(win->ui, ui_path);
    if (!mi || !GTK_IS_MENU_ITEM(mi))
        return NULL;

    submenu = gtk_menu_item_get_submenu(GTK_MENU_ITEM(mi));
    if (!submenu || !GTK_IS_MENU(submenu))
        return NULL;

    if (action_name && win->ag) {
        act = gtk_action_group_get_action(win->ag, action_name);
        if (act)
            label = strip_mnemonic_underscore(gtk_action_get_label(act));
    }

    GtkWidget *btn = gtk_button_new_with_label(label ? label : (fallback_label ? fallback_label : action_name));
    gtk_widget_set_can_focus(btn, FALSE);

    FsOverlayMenuBtn *d = g_new0(FsOverlayMenuBtn, 1);
    d->menu = submenu;

    g_signal_connect_data(btn, "clicked",
                          G_CALLBACK(fs_overlay_menu_button_clicked),
                          d, (GClosureNotify)g_free, 0);

    if (label)
        g_free(label);

    return btn;
}


static void fs_overlay_build(SpiceWindow *win)
{
    GtkWidget *bar_box;
    GtkWidget *btn;
    GtkWidget *mb;

    fs_overlay_css_init();

    win->top_revealer = gtk_revealer_new();
    gtk_revealer_set_transition_type(GTK_REVEALER(win->top_revealer),
                                     GTK_REVEALER_TRANSITION_TYPE_SLIDE_DOWN);
    gtk_revealer_set_transition_duration(GTK_REVEALER(win->top_revealer), 150);
    gtk_revealer_set_reveal_child(GTK_REVEALER(win->top_revealer), FALSE);

    /* Visible bar */
    win->top_bar = gtk_event_box_new();
    gtk_event_box_set_visible_window(GTK_EVENT_BOX(win->top_bar), TRUE);

    /* One centered row: [Disconnect] [Exit Fullscreen] | [Options] [Input] */
    bar_box = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 8);
    gtk_container_set_border_width(GTK_CONTAINER(bar_box), 6);
    gtk_widget_set_halign(bar_box, GTK_ALIGN_CENTER);
    gtk_widget_set_valign(bar_box, GTK_ALIGN_CENTER);
    gtk_widget_set_hexpand(bar_box, FALSE);

    btn = gtk_button_new_with_label(_("Disconnect"));
    g_signal_connect(btn, "clicked", G_CALLBACK(fs_overlay_btn_disconnect_clicked), win);
    gtk_style_context_add_class(gtk_widget_get_style_context(btn), "fs-overlay-danger");
    gtk_box_pack_start(GTK_BOX(bar_box), btn, FALSE, FALSE, 0);

    btn = gtk_button_new_with_label(_("Exit Fullscreen"));
    g_signal_connect(btn, "clicked", G_CALLBACK(fs_overlay_btn_exit_fullscreen_clicked), win);
    gtk_style_context_add_class(gtk_widget_get_style_context(btn), "fs-overlay-danger");
    gtk_box_pack_start(GTK_BOX(bar_box), btn, FALSE, FALSE, 0);

    gtk_box_pack_start(GTK_BOX(bar_box), gtk_separator_new(GTK_ORIENTATION_VERTICAL), FALSE, FALSE, 6);

    mb = fs_overlay_menu_button_new(win, "/MainMenu/OptionMenu", "OptionMenu", _("Options"));
    if (mb)
        gtk_box_pack_start(GTK_BOX(bar_box), mb, FALSE, FALSE, 0);

    mb = fs_overlay_menu_button_new(win, "/MainMenu/InputMenu", "InputMenu", _("Input"));
    if (mb)
        gtk_box_pack_start(GTK_BOX(bar_box), mb, FALSE, FALSE, 0);

    gtk_container_add(GTK_CONTAINER(win->top_bar), bar_box);
    gtk_container_add(GTK_CONTAINER(win->top_revealer), win->top_bar);

    gtk_widget_add_events(win->top_bar, GDK_ENTER_NOTIFY_MASK | GDK_LEAVE_NOTIFY_MASK);
    g_signal_connect(win->top_bar, "enter-notify-event", G_CALLBACK(fs_overlay_bar_enter_cb), win);
    g_signal_connect(win->top_bar, "leave-notify-event", G_CALLBACK(fs_overlay_bar_leave_cb), win);

    /* Hotzone (semi-transparent): only this area triggers showing the bar */
    win->hotzone = gtk_event_box_new();
    gtk_event_box_set_visible_window(GTK_EVENT_BOX(win->hotzone), TRUE);
    gtk_style_context_add_class(gtk_widget_get_style_context(win->hotzone), "fs-overlay-hotzone");
    gtk_widget_set_halign(win->hotzone, GTK_ALIGN_CENTER);
    gtk_widget_set_valign(win->hotzone, GTK_ALIGN_START);
    win->hotzone_width = 420;
    gtk_widget_set_size_request(win->hotzone, win->hotzone_width, 4);
    gtk_widget_set_hexpand(win->hotzone, FALSE);
    gtk_widget_add_events(win->hotzone, GDK_ENTER_NOTIFY_MASK | GDK_LEAVE_NOTIFY_MASK);
    g_signal_connect(win->hotzone, "enter-notify-event", G_CALLBACK(fs_overlay_hotzone_enter_cb), win);
    g_signal_connect(win->hotzone, "leave-notify-event", G_CALLBACK(fs_overlay_hotzone_leave_cb), win);

    /* Keep hotzone width in sync with bar width */
    g_signal_connect(win->top_bar, "size-allocate", G_CALLBACK(fs_overlay_top_bar_size_allocate), win);

    gtk_overlay_add_overlay(GTK_OVERLAY(win->overlay), win->hotzone);
    gtk_overlay_set_overlay_pass_through(GTK_OVERLAY(win->overlay), win->hotzone, FALSE);

    gtk_overlay_add_overlay(GTK_OVERLAY(win->overlay), win->top_revealer);
    gtk_overlay_set_overlay_pass_through(GTK_OVERLAY(win->overlay), win->top_revealer, FALSE);

    /* Keep the overlay controls centered and sized to content.
     * Do NOT let the revealer expand to full width, otherwise the hotzone
     * may inherit full-width allocations on some backends.
     */
    gtk_widget_set_halign(win->top_revealer, GTK_ALIGN_CENTER);
    gtk_widget_set_valign(win->top_revealer, GTK_ALIGN_START);
    gtk_widget_set_hexpand(win->top_revealer, FALSE);
    gtk_widget_set_halign(win->top_bar, GTK_ALIGN_CENTER);
    gtk_widget_set_hexpand(win->top_bar, FALSE);
}
static void grab_keys_pressed_cb(GtkWidget *widget, gpointer data)
{
    SpiceWindow *win = data;

    /* since mnemonics are disabled, we leave fullscreen when
       ungrabbing mouse. Perhaps we should have a different handling
       of fullscreen key, or simply use a UI, like vinagre */
    window_set_fullscreen(win, FALSE);
}

static void mouse_grab_cb(GtkWidget *widget, gint grabbed, gpointer data)
{
    SpiceWindow *win = data;

    win->mouse_grabbed = grabbed;
    update_status(win->conn);
}

static void keyboard_grab_cb(GtkWidget *widget, gint grabbed, gpointer data)
{
    SpiceWindow *win = data;
    GtkSettings *settings = gtk_widget_get_settings (widget);

    if (grabbed) {
        /* disable mnemonics & accels */
        g_object_get(settings,
                     "gtk-enable-accels", &win->enable_accels_save,
                     "gtk-enable-mnemonics", &win->enable_mnemonics_save,
                     NULL);
        g_object_set(settings,
                     "gtk-enable-accels", FALSE,
                     "gtk-enable-mnemonics", FALSE,
                     NULL);
    } else {
        g_object_set(settings,
                     "gtk-enable-accels", win->enable_accels_save,
                     "gtk-enable-mnemonics", win->enable_mnemonics_save,
                     NULL);
    }
}

static void menu_cb_resize_to(GtkAction *action G_GNUC_UNUSED,
                              gpointer data)
{
    SpiceWindow *win = data;
    GtkWidget *dialog;
    GtkWidget *spin_width, *spin_height, *spin_x, *spin_y;
    GtkGrid *grid;
    gint width, height;
    dialog = gtk_dialog_new_with_buttons("Resize guest to",
                                         GTK_WINDOW(win->toplevel),
                                         GTK_DIALOG_DESTROY_WITH_PARENT,
                                         "_Apply",
                                         GTK_RESPONSE_APPLY,
                                         "_Cancel",
                                         GTK_RESPONSE_CANCEL,
                                         NULL);

    spin_width = gtk_spin_button_new_with_range(0, G_MAXINT, 10);
    spin_height = gtk_spin_button_new_with_range(0, G_MAXINT, 10);
    spin_x = gtk_spin_button_new_with_range(0, G_MAXINT, 10);
    spin_y = gtk_spin_button_new_with_range(0, G_MAXINT, 10);

    gtk_widget_get_preferred_width(win->spice, NULL, &width);
    gtk_widget_get_preferred_height(win->spice, NULL, &height);
    width *= gtk_widget_get_scale_factor(win->spice);
    height *= gtk_widget_get_scale_factor(win->spice);

    gtk_spin_button_set_value(GTK_SPIN_BUTTON(spin_width), width);
    gtk_spin_button_set_value(GTK_SPIN_BUTTON(spin_height), height);

    grid = GTK_GRID(gtk_grid_new());
    gtk_container_add(GTK_CONTAINER(gtk_dialog_get_content_area(GTK_DIALOG(dialog))),
                      GTK_WIDGET(grid));
    gtk_grid_attach(grid, gtk_label_new("Resize the guest display:"), 0, 0, 2, 1);
    gtk_grid_attach(grid, gtk_label_new("width:"), 0, 2, 1, 1);
    gtk_grid_attach(grid, spin_width, 1, 2, 1, 1);
    gtk_grid_attach(grid, gtk_label_new("height:"), 0, 3, 1, 1);
    gtk_grid_attach(grid, spin_height, 1, 3, 1, 1);
    gtk_grid_attach(grid, gtk_label_new("x:"), 0, 4, 1, 1);
    gtk_grid_attach(grid, spin_x, 1, 4, 1, 1);
    gtk_grid_attach(grid, gtk_label_new("y:"), 0, 5, 1, 1);
    gtk_grid_attach(grid, spin_y, 1, 5, 1, 1);

    gtk_widget_show_all(dialog);
    if (gtk_dialog_run(GTK_DIALOG (dialog)) == GTK_RESPONSE_APPLY) {
        spice_main_channel_update_display_enabled(win->conn->main, win->id + win->monitor_id, TRUE,
                                                  FALSE);
        spice_main_channel_update_display(
            win->conn->main,
            win->id + win->monitor_id,
            gtk_spin_button_get_value_as_int(GTK_SPIN_BUTTON(spin_x)),
            gtk_spin_button_get_value_as_int(GTK_SPIN_BUTTON(spin_y)),
            gtk_spin_button_get_value_as_int(GTK_SPIN_BUTTON(spin_width)),
            gtk_spin_button_get_value_as_int(GTK_SPIN_BUTTON(spin_height)),
            TRUE);
        spice_main_channel_send_monitor_config(win->conn->main);
    }
    gtk_widget_destroy(dialog);
}

static void restore_configuration(SpiceWindow *win)
{
    gboolean state;
    gchar *str;
    gchar **keys = NULL;
    gsize nkeys, i;
    GError *error = NULL;
    gpointer object;

    keys = g_key_file_get_keys(keyfile, "general", &nkeys, &error);
    if (error != NULL) {
        if (error->code != G_KEY_FILE_ERROR_GROUP_NOT_FOUND)
            g_warning("Failed to read configuration file keys: %s", error->message);
        g_clear_error(&error);
        return;
    }

    if (nkeys > 0)
        g_return_if_fail(keys != NULL);

    for (i = 0; i < nkeys; ++i) {
        if (g_str_equal(keys[i], "grab-sequence"))
            continue;
#ifdef USE_USBREDIR
        if (usb_policy_cli_active && g_str_equal(keys[i], "auto-usbredir"))
            continue;
#endif
        state = g_key_file_get_boolean(keyfile, "general", keys[i], &error);
        if (error != NULL) {
            g_clear_error(&error);
            continue;
        }

        if (is_gtk_session_property(keys[i])) {
            object = win->conn->gtk_session;
        } else {
            object = win->spice;
        }
        g_object_set(object, keys[i], state, NULL);
    }

    g_strfreev(keys);

    str = g_key_file_get_string(keyfile, "general", "grab-sequence", &error);
    if (error == NULL) {
        SpiceGrabSequence *seq = spice_grab_sequence_new_from_string(str);
        spice_display_set_grab_keys(SPICE_DISPLAY(win->spice), seq);
        spice_grab_sequence_free(seq);
        g_free(str);
    }
    g_clear_error(&error);


    state = g_key_file_get_boolean(keyfile, "ui", "toolbar", &error);
    if (error == NULL)
        gtk_widget_set_visible(win->toolbar, state);
    g_clear_error(&error);

    state = g_key_file_get_boolean(keyfile, "ui", "statusbar", &error);
    if (error == NULL)
        gtk_widget_set_visible(win->statusbar, state);
    g_clear_error(&error);
}

/* ------------------------------------------------------------------ */
static const GtkActionEntry entries[] = {
    { .name="ViewMenu",              .label=N_("_View") },
    { .name="InputMenu",             .label=N_("_Input") },
    { .name="OptionMenu",            .label=N_("_Options") },
    { .name="CompressionMenu",       .label=N_("_Preferred image compression") },
    { .name="VideoCodecTypeMenu",    .label=N_("_Preferred video codec type") },

    /* View */
    {
        .name        = "Fullscreen",
        .stock_id    = "view-fullscreen",
        .label       = N_("_Fullscreen"),
        .callback    = G_CALLBACK(menu_cb_fullscreen),
        .accelerator = "<shift>F11",
    },
    {
        .name        = "ResizeTo",
        .label       = N_("_Resize to"),
        .callback    = G_CALLBACK(menu_cb_resize_to),
    },

#ifdef USE_SMARTCARD
    {
        .name        = "InsertSmartcard",
        .label       = N_("_Insert Smartcard"),
        .callback    = G_CALLBACK(menu_cb_insert_smartcard),
        .accelerator = "<shift>F8",
    },
    {
        .name        = "RemoveSmartcard",
        .label       = N_("_Remove Smartcard"),
        .callback    = G_CALLBACK(menu_cb_remove_smartcard),
        .accelerator = "<shift>F9",
    },
#endif

#ifdef USE_USBREDIR
    {
        .name        = "SelectUsbDevices",
        .label       = N_("_Select USB Devices for redirection"),
        .callback    = G_CALLBACK(menu_cb_select_usb_devices),
        .accelerator = "<shift>F10",
    },
#endif

    {
        .name        = "MouseMode",
        .label       = N_("Toggle _mouse mode"),
        .callback    = G_CALLBACK(menu_cb_mouse_mode),
        .accelerator = "<shift>F7",
    }
};

static const char *spice_display_properties[] = {
    "grab-keyboard",
    "grab-mouse",
    "resize-guest",
    "scaling",
    "disable-inputs",
};

static const char *spice_gtk_session_properties[] = {
    "auto-clipboard",
    "auto-usbredir",
    "sync-modifiers",
};

static const GtkToggleActionEntry tentries[] = {
    {
        .name        = "grab-keyboard",
        .label       = N_("Grab keyboard when active and focused"),
        .callback    = G_CALLBACK(menu_cb_bool_prop),
    },{
        .name        = "grab-mouse",
        .label       = N_("Grab mouse in server mode (no tablet/vdagent)"),
        .callback    = G_CALLBACK(menu_cb_bool_prop),
    },{
        .name        = "resize-guest",
        .label       = N_("Resize guest to match window size"),
        .callback    = G_CALLBACK(menu_cb_bool_prop),
    },{
        .name        = "scaling",
        .label       = N_("Scale display"),
        .callback    = G_CALLBACK(menu_cb_bool_prop),
    },{
        .name        = "disable-inputs",
        .label       = N_("Disable inputs"),
        .callback    = G_CALLBACK(menu_cb_bool_prop),
    },{
        .name        = "sync-modifiers",
        .label       = N_("Sync modifiers"),
        .callback    = G_CALLBACK(menu_cb_bool_prop),
    },{
        .name        = "auto-clipboard",
        .label       = N_("Automatic clipboard sharing between host and guest"),
        .callback    = G_CALLBACK(menu_cb_bool_prop),
    },{
        .name        = "auto-usbredir",
        .label       = N_("Auto redirect newly plugged in USB devices"),
        .callback    = G_CALLBACK(menu_cb_bool_prop),
        .is_active   = TRUE,
    },{
        .name        = "Statusbar",
        .label       = N_("Statusbar"),
        .callback    = G_CALLBACK(menu_cb_statusbar),
    },{
        .name        = "Toolbar",
        .label       = N_("Toolbar"),
        .callback    = G_CALLBACK(menu_cb_toolbar),
    }
};

static const GtkRadioActionEntry compression_entries[] = {
    {
        .name  = "auto-glz",
        .label       = N_("auto-glz"),
        .value = SPICE_IMAGE_COMPRESSION_AUTO_GLZ,
    },{
        .name  = "auto-lz",
        .label       = N_("auto-lz"),
        .value = SPICE_IMAGE_COMPRESSION_AUTO_LZ,
    },{
        .name  = "quic",
        .label       = N_("quic"),
        .value = SPICE_IMAGE_COMPRESSION_QUIC,
    },{
        .name  = "glz",
        .label       = N_("glz"),
        .value = SPICE_IMAGE_COMPRESSION_GLZ,
    },{
        .name  = "lz",
        .label       = N_("lz"),
        .value = SPICE_IMAGE_COMPRESSION_LZ,
    },{
#ifdef USE_LZ4
        .name  = "lz4",
        .label       = N_("lz4"),
        .value = SPICE_IMAGE_COMPRESSION_LZ4,
    },{
#endif
        .name  = "off",
        .label       = N_("off"),
        .value = SPICE_IMAGE_COMPRESSION_OFF,
    }
};

static const GtkRadioActionEntry video_codec_type_entries[] = {
    {
        .name  = "av1",
        .label       = N_("av1"),
        .value = SPICE_VIDEO_CODEC_TYPE_AV1,
    },{
        .name  = "mjpeg",
        .label       = N_("mjpeg"),
        .value = SPICE_VIDEO_CODEC_TYPE_MJPEG,
    },{
        .name  = "vp8",
        .label       = N_("vp8"),
        .value = SPICE_VIDEO_CODEC_TYPE_VP8,
    },{
        .name  = "vp9",
        .label       = N_("vp9"),
        .value = SPICE_VIDEO_CODEC_TYPE_VP9,
    },{
        .name  = "h264",
        .label       = N_("h264"),
        .value = SPICE_VIDEO_CODEC_TYPE_H264,
    },{
        .name  = "h265",
        .label       = N_("h265"),
        .value = SPICE_VIDEO_CODEC_TYPE_H265,
    }
};

static char ui_xml[] =
"<ui>\n"
"  <menubar action='MainMenu'>\n"
"    <menu action='OptionMenu'>\n"
"      <menuitem action='grab-keyboard'/>\n"
"      <menuitem action='grab-mouse'/>\n"
"      <menuitem action='MouseMode'/>\n"
"      <menuitem action='resize-guest'/>\n"
"      <menuitem action='scaling'/>\n"
"      <menuitem action='disable-inputs'/>\n"
"      <menuitem action='sync-modifiers'/>\n"
"      <menuitem action='auto-clipboard'/>\n"
"      <menuitem action='auto-usbredir'/>\n"
"      <menu action='CompressionMenu'>\n"
"        <menuitem action='auto-glz'/>\n"
"        <menuitem action='auto-lz'/>\n"
"        <menuitem action='quic'/>\n"
"        <menuitem action='glz'/>\n"
"        <menuitem action='lz'/>\n"
#ifdef USE_LZ4
"        <menuitem action='lz4'/>\n"
#endif
"        <menuitem action='off'/>\n"
"      </menu>\n"
"      <menu action='VideoCodecTypeMenu'>\n"
"        <menuitem action='av1'/>\n"
"        <menuitem action='mjpeg'/>\n"
"        <menuitem action='vp8'/>\n"
"        <menuitem action='vp9'/>\n"
"        <menuitem action='h264'/>\n"
"        <menuitem action='h265'/>\n"
"      </menu>\n"
"    </menu>\n"
"    <menu action='ViewMenu'>\n"
"      <menuitem action='Fullscreen'/>\n"
"      <menuitem action='Toolbar'/>\n"
"      <menuitem action='Statusbar'/>\n"
"    </menu>\n"
"    <menu action='InputMenu'>\n"
#ifdef USE_SMARTCARD
"      <menuitem action='InsertSmartcard'/>\n"
"      <menuitem action='RemoveSmartcard'/>\n"
#endif
#ifdef USE_USBREDIR
"      <menuitem action='SelectUsbDevices'/>\n"
#endif
"    </menu>\n"
"  </menubar>\n"
"  <toolbar action='ToolBar'>\n"
"    <toolitem action='Fullscreen'/>\n"
"    <toolitem action='ResizeTo'/>\n"
"  </toolbar>\n"
"</ui>\n";

static gboolean is_gtk_session_property(const gchar *property)
{
    int i;

    for (i = 0; i < G_N_ELEMENTS(spice_gtk_session_properties); i++) {
        if (!strcmp(spice_gtk_session_properties[i], property)) {
            return TRUE;
        }
    }
    return FALSE;
}

static void recent_item_activated_cb(GtkRecentChooser *chooser, gpointer data)
{
    GtkRecentInfo *info;
    struct spice_connection *conn;
    const char *uri;

    info = gtk_recent_chooser_get_current_item(chooser);

    uri = gtk_recent_info_get_uri(info);
    g_return_if_fail(uri != NULL);

    conn = connection_new();
    g_object_set(conn->session, "uri", uri, NULL);
    gtk_recent_info_unref(info);
    connection_connect(conn);
}

static void compression_cb(GtkRadioAction *action G_GNUC_UNUSED,
                           GtkRadioAction *current,
                           gpointer user_data)
{
    spice_display_channel_change_preferred_compression(SPICE_CHANNEL(user_data),
                                                       gtk_radio_action_get_current_value(current));
}

static void video_codec_type_cb(GtkRadioAction *action G_GNUC_UNUSED,
                                GtkRadioAction *current,
                                gpointer user_data)
{
    static GArray *preferred_codecs = NULL;
    gint selected_codec = gtk_radio_action_get_current_value(current);
    guint i;
    GError *err = NULL;

    if (!preferred_codecs) {
        preferred_codecs = g_array_sized_new(FALSE, FALSE,
                                             sizeof(gint),
                                             G_N_ELEMENTS(video_codec_type_entries));
        /* initialize with the menu ordering */
        for (i = 0; i < G_N_ELEMENTS(video_codec_type_entries); i++) {
            g_array_append_val(preferred_codecs, video_codec_type_entries[i].value);
        }
    }

    /* remove codec from array and insert at the beginning */
    for (i = 0; i < preferred_codecs->len &&
                g_array_index(preferred_codecs, gint, i) != selected_codec; i++);

    g_assert(i < preferred_codecs->len);
    g_array_remove_index(preferred_codecs, i);
    g_array_prepend_val(preferred_codecs, selected_codec);

    if (!spice_display_channel_change_preferred_video_codec_types(SPICE_CHANNEL(user_data),
                                                                  (gint *) preferred_codecs->data,
                                                                  preferred_codecs->len, &err)) {
        g_warning("setting preferred video codecs failed: %s", err->message);
        g_error_free(err);
    }
}

static void
spice_window_class_init (SpiceWindowClass *klass)
{
}

static void
spice_window_init (SpiceWindow *self)
{
}

static SpiceWindow *create_spice_window(spice_connection *conn, SpiceChannel *channel, int id, gint monitor_id)
{
    char title[32];
    SpiceWindow *win;
    GtkAction *toggle;
    gboolean state;
    GtkWidget *vbox, *frame;
    GError *err = NULL;
    int i;
    SpiceGrabSequence *seq;

    win = g_object_new(SPICE_TYPE_WINDOW, NULL);
    win->id = id;
    win->monitor_id = monitor_id;
    win->conn = conn;
    win->display_channel = channel;

    /* toplevel */
    win->toplevel = gtk_window_new(GTK_WINDOW_TOPLEVEL);
    if (spicy_title == NULL) {
        snprintf(title, sizeof(title), _("Connect to VM %d:%d"), id, monitor_id);
    } else {
        snprintf(title, sizeof(title), "%s", spicy_title);
    }

    gtk_window_set_title(GTK_WINDOW(win->toplevel), title);
    g_signal_connect(G_OBJECT(win->toplevel), "window-state-event",
                     G_CALLBACK(window_state_cb), win);
    g_signal_connect(G_OBJECT(win->toplevel), "delete-event",
                     G_CALLBACK(delete_cb), win);

/* menu + toolbar */
win->ui = gtk_ui_manager_new();
win->ag = gtk_action_group_new("MenuActions");
gtk_action_group_set_translation_domain(win->ag, GETTEXT_PACKAGE);

gtk_action_group_add_actions(win->ag, entries, G_N_ELEMENTS(entries), win);
gtk_action_group_add_toggle_actions(win->ag, tentries, G_N_ELEMENTS(tentries), win);

gtk_action_group_add_radio_actions(win->ag,
                                   compression_entries,
                                   G_N_ELEMENTS(compression_entries),
                                   -1,
                                   G_CALLBACK(compression_cb),
                                   win->display_channel);

if (!spice_channel_test_capability(win->display_channel, SPICE_DISPLAY_CAP_PREF_COMPRESSION)) {
    GtkAction *compression_menu_action =
        gtk_action_group_get_action(win->ag, "CompressionMenu");
    gtk_action_set_sensitive(compression_menu_action, FALSE);
}

gtk_action_group_add_radio_actions(win->ag,
                                   video_codec_type_entries,
                                   G_N_ELEMENTS(video_codec_type_entries),
                                   -1,
                                   G_CALLBACK(video_codec_type_cb),
                                   win->display_channel);

if (!spice_channel_test_capability(win->display_channel,
                                   SPICE_DISPLAY_CAP_PREF_VIDEO_CODEC_TYPE)) {
    GtkAction *video_codec_type_menu_action =
        gtk_action_group_get_action(win->ag, "VideoCodecTypeMenu");
    gtk_action_set_sensitive(video_codec_type_menu_action, FALSE);
}

gtk_ui_manager_insert_action_group(win->ui, win->ag, 0);
gtk_window_add_accel_group(GTK_WINDOW(win->toplevel),
                           gtk_ui_manager_get_accel_group(win->ui));

err = NULL;
if (!gtk_ui_manager_add_ui_from_string(win->ui, ui_xml, -1, &err)) {
    g_warning("building menus failed: %s", err->message);
    g_error_free(err);
    exit(1);
}


win->menubar = gtk_ui_manager_get_widget(win->ui, "/MainMenu");
win->toolbar = gtk_ui_manager_get_widget(win->ui, "/ToolBar");

/* Выбрать H.264 по умолчанию и вызвать callback только если капабилити есть */
if (spice_channel_test_capability(win->display_channel,
                                  SPICE_DISPLAY_CAP_PREF_VIDEO_CODEC_TYPE)) {
    GtkAction *act_h264 = gtk_action_group_get_action(win->ag, "h264");
    if (act_h264) {
        gtk_toggle_action_set_active(GTK_TOGGLE_ACTION(act_h264), TRUE);
    }
}


    /* recent menu */
    win->ritem  = gtk_ui_manager_get_widget
        (win->ui, "/MainMenu/FileMenu/FileRecentMenu");

    GtkRecentFilter  *rfilter;

    win->rmenu = gtk_recent_chooser_menu_new();
    gtk_recent_chooser_set_show_icons(GTK_RECENT_CHOOSER(win->rmenu), FALSE);
    rfilter = gtk_recent_filter_new();
    gtk_recent_filter_add_mime_type(rfilter, "application/x-spice");
    gtk_recent_chooser_add_filter(GTK_RECENT_CHOOSER(win->rmenu), rfilter);
    gtk_recent_chooser_set_local_only(GTK_RECENT_CHOOSER(win->rmenu), FALSE);
    gtk_menu_item_set_submenu(GTK_MENU_ITEM(win->ritem), win->rmenu);
    g_signal_connect(win->rmenu, "item-activated",
                     G_CALLBACK(recent_item_activated_cb), win);

    /* spice display */
    win->spice = GTK_WIDGET(spice_display_new_with_monitor(conn->session, id, monitor_id));

    /* Fullscreen overlay container (Spice display + top auto-hide bar) */
    win->overlay = gtk_overlay_new();
    gtk_container_add(GTK_CONTAINER(win->overlay), win->spice);
    fs_overlay_build(win);

    /* Track pointer to show/hide overlay in fullscreen */
    gtk_widget_add_events(win->toplevel, GDK_POINTER_MOTION_MASK | GDK_LEAVE_NOTIFY_MASK);

    seq = spice_grab_sequence_new_from_string("Shift_L+F12");
    spice_display_set_grab_keys(SPICE_DISPLAY(win->spice), seq);
    spice_grab_sequence_free(seq);

    g_signal_connect(G_OBJECT(win->spice), "mouse-grab",
                     G_CALLBACK(mouse_grab_cb), win);
    g_signal_connect(G_OBJECT(win->spice), "keyboard-grab",
                     G_CALLBACK(keyboard_grab_cb), win);
    g_signal_connect(G_OBJECT(win->spice), "grab-keys-pressed",
                     G_CALLBACK(grab_keys_pressed_cb), win);

    /* status line */
    win->statusbar = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 1);

    win->status = gtk_label_new("status line");
    gtk_misc_set_alignment(GTK_MISC(win->status), 0, 0.5);
    gtk_misc_set_padding(GTK_MISC(win->status), 3, 1);
    update_status_window(win);

    frame = gtk_frame_new(NULL);
    gtk_box_pack_start(GTK_BOX(win->statusbar), frame, TRUE, TRUE, 0);
    gtk_container_add(GTK_CONTAINER(frame), win->status);

    for (i = 0; i < STATE_MAX; i++) {
        win->st[i] = gtk_label_new("?");
        gtk_label_set_width_chars(GTK_LABEL(win->st[i]), 5);
        frame = gtk_frame_new(NULL);
        gtk_box_pack_end(GTK_BOX(win->statusbar), frame, FALSE, FALSE, 0);
        gtk_container_add(GTK_CONTAINER(frame), win->st[i]);
    }

    /* Make a vbox and put stuff in */
    vbox = gtk_box_new(GTK_ORIENTATION_VERTICAL, 1);
    gtk_container_set_border_width(GTK_CONTAINER(vbox), 0);
    gtk_container_add(GTK_CONTAINER(win->toplevel), vbox);
    gtk_box_pack_start(GTK_BOX(vbox), win->menubar, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(vbox), win->toolbar, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(vbox), win->overlay, TRUE, TRUE, 0);
    gtk_box_pack_end(GTK_BOX(vbox), win->statusbar, FALSE, TRUE, 0);

    /* show window */
    if (fullscreen)
        gtk_window_fullscreen(GTK_WINDOW(win->toplevel));

    gtk_widget_show_all(vbox);
    restore_configuration(win);

    /* init toggle actions */
    for (i = 0; i < G_N_ELEMENTS(spice_display_properties); i++) {
        toggle = gtk_action_group_get_action(win->ag,
                                             spice_display_properties[i]);
        g_object_get(win->spice, spice_display_properties[i], &state, NULL);
        gtk_toggle_action_set_active(GTK_TOGGLE_ACTION(toggle), state);
    }

    for (i = 0; i < G_N_ELEMENTS(spice_gtk_session_properties); i++) {
        char notify[64];

        toggle = gtk_action_group_get_action(win->ag,
                                             spice_gtk_session_properties[i]);
        g_object_get(win->conn->gtk_session, spice_gtk_session_properties[i],
                     &state, NULL);
        gtk_toggle_action_set_active(GTK_TOGGLE_ACTION(toggle), state);

        snprintf(notify, sizeof(notify), "notify::%s",
                 spice_gtk_session_properties[i]);
        spice_g_signal_connect_object(win->conn->gtk_session, notify,
                                      G_CALLBACK(menu_cb_conn_bool_prop_changed),
                                      win, 0);
    }

#ifdef USE_USBREDIR
    if (usb_policy_cli_active) {
        GtkAction *usb_auto_action;

        usb_auto_action = gtk_action_group_get_action(win->ag, "auto-usbredir");
        if (usb_auto_action) {
            gboolean usb_auto_state = FALSE;

            g_object_get(win->conn->gtk_session, "auto-usbredir",
                         &usb_auto_state, NULL);
            gtk_toggle_action_set_active(GTK_TOGGLE_ACTION(usb_auto_action),
                                         usb_auto_state);
            gtk_action_set_sensitive(usb_auto_action, FALSE);
        }
    }
#endif

    update_edit_menu_window(win);

    toggle = gtk_action_group_get_action(win->ag, "Toolbar");
    state = gtk_widget_get_visible(win->toolbar);
    gtk_toggle_action_set_active(GTK_TOGGLE_ACTION(toggle), state);

    toggle = gtk_action_group_get_action(win->ag, "Statusbar");
    state = gtk_widget_get_visible(win->statusbar);
    gtk_toggle_action_set_active(GTK_TOGGLE_ACTION(toggle), state);

#ifdef USE_SMARTCARD
    gboolean smartcard;

    enable_smartcard_actions(win, NULL, FALSE, FALSE);
    g_object_get(G_OBJECT(conn->session),
                 "enable-smartcard", &smartcard,
                 NULL);
    if (smartcard) {
        g_signal_connect(G_OBJECT(spice_smartcard_manager_get()), "reader-added",
                         (GCallback)reader_added_cb, win);
        g_signal_connect(G_OBJECT(spice_smartcard_manager_get()), "reader-removed",
                         (GCallback)reader_removed_cb, win);
        g_signal_connect(G_OBJECT(spice_smartcard_manager_get()), "card-inserted",
                         (GCallback)card_inserted_cb, win);
        g_signal_connect(G_OBJECT(spice_smartcard_manager_get()), "card-removed",
                         (GCallback)card_removed_cb, win);
    }
#endif

#ifndef USE_USBREDIR
    GtkAction *usbredir = gtk_action_group_get_action(win->ag, "auto-usbredir");
    gtk_action_set_visible(usbredir, FALSE);
#endif

    gtk_widget_grab_focus(win->spice);

    return win;
}

static void destroy_spice_window(SpiceWindow *win)
{
    if (win == NULL)
        return;

    win->destroying = TRUE;

    fs_overlay_cancel_hide(win);

    if (win->toplevel && GTK_IS_WIDGET(win->toplevel))
        g_signal_handlers_disconnect_by_data(win->toplevel, win);
    if (win->spice && GTK_IS_WIDGET(win->spice))
        g_signal_handlers_disconnect_by_data(win->spice, win);
    if (win->top_bar && GTK_IS_WIDGET(win->top_bar))
        g_signal_handlers_disconnect_by_data(win->top_bar, win);

    SPICE_DEBUG("destroy window (#%d:%d)", win->id, win->monitor_id);

    if (win->ag) {
        g_object_unref(win->ag);
        win->ag = NULL;
    }
    if (win->ui) {
        g_object_unref(win->ui);
        win->ui = NULL;
    }

    if (win->toplevel && GTK_IS_WIDGET(win->toplevel))
        gtk_widget_destroy(win->toplevel);
    win->toplevel = NULL;

    g_object_unref(win);
}

/* ------------------------------------------------------------------ */

static void recent_add(SpiceSession *session)
{
    GtkRecentManager *recent;
    GtkRecentData meta = {
        .mime_type    = (char*)"application/x-spice",
        .app_name     = (char*)"spicy",
        .app_exec     = (char*)"spicy --uri=%u",
    };
    char *uri;

    g_object_get(session, "uri", &uri, NULL);
    SPICE_DEBUG("%s: %s", __FUNCTION__, uri);

    recent = gtk_recent_manager_get_default();
    if (g_str_has_prefix(uri, "spice://"))
        meta.display_name = uri + 8;
    else if (g_str_has_prefix(uri, "spice+unix://"))
        meta.display_name = uri + 13;
    else
        g_return_if_reached();

    if (!gtk_recent_manager_add_full(recent, uri, &meta))
        g_warning("Recent item couldn't be added successfully");

    g_free(uri);
}

static void main_channel_event(SpiceChannel *channel, SpiceChannelEvent event,
                               gpointer data)
{
    const GError *error = NULL;
    spice_connection *conn = data;
    char password[64];
    int rc;

    switch (event) {
    case SPICE_CHANNEL_OPENED:
        g_message("main channel: opened");
        recent_add(conn->session);
        break;
    case SPICE_CHANNEL_SWITCHING:
        g_message("main channel: switching host");
        break;
    case SPICE_CHANNEL_CLOSED:
        /* this event is only sent if the channel was succesfully opened before */
        g_message("main channel: closed");
        connection_disconnect(conn);
        break;
    case SPICE_CHANNEL_ERROR_IO:
        connection_disconnect(conn);
        break;
    case SPICE_CHANNEL_ERROR_TLS:
    case SPICE_CHANNEL_ERROR_LINK:
    case SPICE_CHANNEL_ERROR_CONNECT:
        error = spice_channel_get_error(channel);
        g_message("main channel: failed to connect");
        if (error) {
            g_message("channel error: %s", error->message);
        }

        if (spicy_connect_dialog(conn->session)) {
            connection_connect(conn);
        } else {
            connection_disconnect(conn);
        }
        break;
    case SPICE_CHANNEL_ERROR_AUTH:
        g_warning("main channel: auth failure (wrong password?)");
        strcpy(password, "");
        /* FIXME i18 */
        rc = ask_user(NULL, "Authentication",
                      "Please enter the spice server password",
                      password, sizeof(password), true);
        if (rc == 0) {
            g_object_set(conn->session, "password", password, NULL);
            connection_connect(conn);
        } else {
            connection_disconnect(conn);
        }
        break;
    default:
        /* TODO: more sophisticated error handling */
        g_warning("unknown main channel event: %u", event);
        /* connection_disconnect(conn); */
        break;
    }
}

//static void main_mouse_update(SpiceChannel *channel, gpointer data)
//{
//    spice_connection *conn = data;
//    gint mode;
//
//    g_object_get(channel, "mouse-mode", &mode, NULL);
//    switch (mode) {
//    case SPICE_MOUSE_MODE_SERVER:
//        conn->mouse_state = "server";
//        break;
//    case SPICE_MOUSE_MODE_CLIENT:
//        conn->mouse_state = "client";
//        break;
//    default:
//        conn->mouse_state = "?";
//        break;
//    }
//    update_status(conn);
//}

//static void main_agent_update(SpiceChannel *channel, gpointer data)
//{
//    spice_connection *conn = data;
//
//    g_object_get(channel, "agent-connected", &conn->agent_connected, NULL);
//    conn->agent_state = conn->agent_connected ? "yes" : "no";
//    update_status(conn);
//    update_edit_menu(conn);
//}
static void main_mouse_update(SpiceChannel *channel, gpointer data)
{
    spice_connection *conn = data;
    gint mode;

    g_object_get(channel, "mouse-mode", &mode, NULL);
    switch (mode) {
    case SPICE_MOUSE_MODE_SERVER:
        conn->mouse_state = _("server");
        break;
    case SPICE_MOUSE_MODE_CLIENT:
        conn->mouse_state = _("client");
        break;
    default:
        conn->mouse_state = _("unknown");
        break;
    }
    update_status(conn);
}
    
static void main_agent_update(SpiceChannel *channel, gpointer data)
{
    spice_connection *conn = data;

    g_object_get(channel, "agent-connected", &conn->agent_connected, NULL);
    conn->agent_state = conn->agent_connected ? _("yes") : _("no");

    update_status(conn);
    update_edit_menu(conn);
}

static void inputs_modifiers(SpiceChannel *channel, gpointer data)
{
    spice_connection *conn = data;
    int m, i;

    g_object_get(channel, "key-modifiers", &m, NULL);
    for (i = 0; i < SPICE_N_ELEMENTS(conn->wins); i++) {
        if (conn->wins[i] == NULL)
            continue;

        gtk_label_set_text(GTK_LABEL(conn->wins[i]->st[STATE_SCROLL_LOCK]),
                           m & SPICE_KEYBOARD_MODIFIER_FLAGS_SCROLL_LOCK ? "SCROLL" : "");
        gtk_label_set_text(GTK_LABEL(conn->wins[i]->st[STATE_CAPS_LOCK]),
                           m & SPICE_KEYBOARD_MODIFIER_FLAGS_CAPS_LOCK ? "CAPS" : "");
        gtk_label_set_text(GTK_LABEL(conn->wins[i]->st[STATE_NUM_LOCK]),
                           m & SPICE_KEYBOARD_MODIFIER_FLAGS_NUM_LOCK ? "NUM" : "");
    }
}

static void display_mark(SpiceChannel *channel, gint mark, SpiceWindow *win)
{
    g_return_if_fail(win != NULL);
    g_return_if_fail(win->toplevel != NULL);

    if (mark == TRUE) {
        gtk_widget_show(win->toplevel);
    } else {
        gtk_widget_hide(win->toplevel);
    }
}

static void update_auto_usbredir_sensitive(spice_connection *conn)
{
#ifdef USE_USBREDIR
    int i;
    GtkAction *ac;
    gboolean sensitive;

    sensitive = spice_session_has_channel_type(conn->session,
                                               SPICE_CHANNEL_USBREDIR);
    for (i = 0; i < SPICE_N_ELEMENTS(conn->wins); i++) {
        if (conn->wins[i] == NULL)
            continue;
        ac = gtk_action_group_get_action(conn->wins[i]->ag, "auto-usbredir");
        gtk_action_set_sensitive(ac, sensitive);
    }
#endif
}

static SpiceWindow* get_window(spice_connection *conn, int channel_id, int monitor_id)
{
    g_return_val_if_fail(channel_id < CHANNELID_MAX, NULL);
    g_return_val_if_fail(monitor_id < MONITORID_MAX, NULL);

    return conn->wins[channel_id * CHANNELID_MAX + monitor_id];
}

static void add_window(spice_connection *conn, SpiceWindow *win)
{
    g_return_if_fail(win != NULL);
    g_return_if_fail(win->id < CHANNELID_MAX);
    g_return_if_fail(win->monitor_id < MONITORID_MAX);
    g_return_if_fail(conn->wins[win->id * CHANNELID_MAX + win->monitor_id] == NULL);

    SPICE_DEBUG("add display monitor %d:%d", win->id, win->monitor_id);
    conn->wins[win->id * CHANNELID_MAX + win->monitor_id] = win;
}

static void del_window(spice_connection *conn, SpiceWindow *win)
{
    if (win == NULL)
        return;

    g_return_if_fail(win->id < CHANNELID_MAX);
    g_return_if_fail(win->monitor_id < MONITORID_MAX);

    g_debug("del display monitor %d:%d", win->id, win->monitor_id);
    conn->wins[win->id * CHANNELID_MAX + win->monitor_id] = NULL;
    if (win->id > 0)
        spice_main_channel_update_display_enabled(conn->main, win->id, FALSE, TRUE);
    else
        spice_main_channel_update_display_enabled(conn->main, win->monitor_id, FALSE, TRUE);
    spice_main_channel_send_monitor_config(conn->main);

    destroy_spice_window(win);
}

static void display_monitors(SpiceChannel *display, GParamSpec *pspec,
                             spice_connection *conn)
{
    GArray *monitors = NULL;
    int id;
    guint i;

    g_object_get(display,
                 "channel-id", &id,
                 "monitors", &monitors,
                 NULL);
    g_return_if_fail(monitors != NULL);

    for (i = 0; i < monitors->len; i++) {
        SpiceWindow *w;

        if (!get_window(conn, id, i)) {
            w = create_spice_window(conn, display, id, i);
            add_window(conn, w);
            spice_g_signal_connect_object(display, "display-mark",
                                          G_CALLBACK(display_mark), w, 0);
            gtk_widget_show(w->toplevel);
            update_auto_usbredir_sensitive(conn);
        }
    }

    for (; i < MONITORID_MAX; i++)
        del_window(conn, get_window(conn, id, i));

    g_clear_pointer(&monitors, g_array_unref);
}

static void port_write_cb(GObject *source_object,
                          GAsyncResult *res,
                          gpointer user_data)
{
    SpicePortChannel *port = SPICE_PORT_CHANNEL(source_object);
    GError *error = NULL;

    spice_port_channel_write_finish(port, res, &error);
    if (error != NULL)
        g_debug("%s", error->message);
    g_clear_error(&error);
}

static void port_flushed_cb(GObject *source_object,
                            GAsyncResult *res,
                            gpointer user_data)
{
    SpiceChannel *channel = SPICE_CHANNEL(source_object);
    GError *error = NULL;

    spice_channel_flush_finish(channel, res, &error);
    if (error != NULL)
        g_debug("%s", error->message);
    g_clear_error(&error);

    spice_channel_disconnect(channel, SPICE_CHANNEL_CLOSED);
}

static gboolean input_cb(GIOChannel *gin, GIOCondition condition, gpointer data)
{
    char buf[4096];
    gsize bytes_read;
    GIOStatus status;

    if (!(condition & G_IO_IN))
        return FALSE;

    status = g_io_channel_read_chars(gin, buf, sizeof(buf), &bytes_read, NULL);
    if (status != G_IO_STATUS_NORMAL)
        return FALSE;

    if (stdin_port != NULL)
        spice_port_channel_write_async(stdin_port, buf, bytes_read, NULL, port_write_cb, NULL);

    return TRUE;
}

static void watch_stdin(void);

static void port_opened(SpiceChannel *channel, GParamSpec *pspec,
                        spice_connection *conn)
{
    SpicePortChannel *port = SPICE_PORT_CHANNEL(channel);
    gchar *name = NULL;
    gboolean opened = FALSE;

    g_object_get(channel,
                 "port-name", &name,
                 "port-opened", &opened,
                 NULL);

    if (opened) {
        /* only send a break event and disconnect */
        if (g_strcmp0(name, "org.spice.spicy.break") == 0) {
            spice_port_channel_event(port, SPICE_PORT_EVENT_BREAK);
            spice_channel_flush_async(channel, NULL, port_flushed_cb, conn);
        }

        /* handle the first spicy port and connect it to stdin/out */
        if (g_strcmp0(name, "org.spice.spicy") == 0 && stdin_port == NULL) {
            watch_stdin();
            stdin_port = port;
        }
    } else {
        if (port == stdin_port)
            stdin_port = NULL;
    }

    g_free(name);
}

static void port_data(SpicePortChannel *port,
                      gpointer data, int size, spice_connection *conn)
{
    int r;

    if (port != stdin_port)
        return;

    r = write(fileno(stdout), data, size);
    if (r != size) {
        g_warning("port write failed result %d/%d errno %d", r, size, errno);
    }
}

typedef struct {
    GtkWidget *vbox;
    GtkWidget *hbox;
    GtkWidget *progress;
    GtkWidget *label;
    GtkWidget *cancel;
} TransferTaskWidgets;

static void transfer_update_progress(GObject *object,
                                     GParamSpec *pspec,
                                     gpointer user_data)
{
    spice_connection *conn = user_data;
    TransferTaskWidgets *widgets = g_hash_table_lookup(conn->transfers, object);
    g_return_if_fail(widgets);
    gtk_progress_bar_set_fraction(GTK_PROGRESS_BAR(widgets->progress),
                                  spice_file_transfer_task_get_progress(SPICE_FILE_TRANSFER_TASK(object)));
}

static void transfer_task_finished(SpiceFileTransferTask *task, GError *error, spice_connection *conn)
{
    if (error)
        g_warning("%s", error->message);
    g_hash_table_remove(conn->transfers, task);
    if (!g_hash_table_size(conn->transfers))
        gtk_widget_hide(conn->transfer_dialog);
}

static gboolean dialog_delete_cb(GtkWidget *widget,
                                 GdkEvent *event G_GNUC_UNUSED,
                                 gpointer user_data G_GNUC_UNUSED)
{
    gtk_dialog_response(GTK_DIALOG(widget), GTK_RESPONSE_CANCEL);
    return TRUE;
}

static void dialog_response_cb(GtkDialog *dialog,
                               gint response_id,
                               gpointer user_data)
{
    spice_connection *conn = user_data;
    g_debug("dialog response: %i", response_id);

    if (response_id == GTK_RESPONSE_CANCEL) {
        GHashTableIter iter;
        gpointer key, value;

        g_hash_table_iter_init(&iter, conn->transfers);
        while (g_hash_table_iter_next(&iter, &key, &value)) {
            SpiceFileTransferTask *task = key;
            spice_file_transfer_task_cancel(task);
        }
    }
}

static void
task_cancel_cb(GtkButton *button,
               gpointer user_data)
{
    SpiceFileTransferTask *task = SPICE_FILE_TRANSFER_TASK(user_data);
    spice_file_transfer_task_cancel(task);
}

static TransferTaskWidgets *
transfer_task_widgets_new(SpiceFileTransferTask *task)
{
    char *filename;
    TransferTaskWidgets *widgets = g_new0(TransferTaskWidgets, 1);

    widgets->vbox = gtk_box_new(GTK_ORIENTATION_VERTICAL, 0);
    widgets->hbox = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 6);
    widgets->cancel = gtk_button_new_with_label("Cancel");

    widgets->progress = gtk_progress_bar_new();
    filename = spice_file_transfer_task_get_filename(task);
    widgets->label = gtk_label_new(filename);
    g_free(filename);

    gtk_widget_set_halign(widgets->label, GTK_ALIGN_START);
    gtk_widget_set_valign(widgets->label, GTK_ALIGN_BASELINE);
    gtk_widget_set_valign(widgets->progress, GTK_ALIGN_CENTER);
    gtk_widget_set_hexpand(widgets->progress, TRUE);
    gtk_widget_set_valign(widgets->cancel, GTK_ALIGN_CENTER);
    gtk_widget_set_hexpand(widgets->progress, FALSE);

    gtk_box_pack_start(GTK_BOX(widgets->hbox), widgets->progress,
                       TRUE, TRUE, 0);
    gtk_box_pack_start(GTK_BOX(widgets->hbox), widgets->cancel,
                       FALSE, TRUE, 0);

    gtk_box_pack_start(GTK_BOX(widgets->vbox), widgets->label,
                       TRUE, TRUE, 0);
    gtk_box_pack_start(GTK_BOX(widgets->vbox), widgets->hbox,
                       TRUE, TRUE, 0);

    g_signal_connect(widgets->cancel, "clicked",
                     G_CALLBACK(task_cancel_cb), task);

    gtk_widget_show_all(widgets->vbox);

    return widgets;
}

static void
transfer_task_widgets_free(TransferTaskWidgets *widgets)
{
    /* child widgets will be destroyed automatically */
    gtk_widget_destroy(widgets->vbox);
    g_free(widgets);
}

static void spice_connection_add_task(spice_connection *conn, SpiceFileTransferTask *task)
{
    TransferTaskWidgets *widgets;
    GtkWidget *content = NULL;

    g_signal_connect(task, "notify::progress",
                     G_CALLBACK(transfer_update_progress), conn);
    g_signal_connect(task, "finished",
                     G_CALLBACK(transfer_task_finished), conn);
    if (!conn->transfer_dialog) {
        conn->transfer_dialog = gtk_dialog_new_with_buttons("File Transfers",
                                                            GTK_WINDOW(conn->wins[0]->toplevel), 0,
                                                            "Cancel", GTK_RESPONSE_CANCEL, NULL);
        gtk_dialog_set_default_response(GTK_DIALOG(conn->transfer_dialog),
                                        GTK_RESPONSE_CANCEL);
        gtk_window_set_resizable(GTK_WINDOW(conn->transfer_dialog), FALSE);
        g_signal_connect(conn->transfer_dialog, "response",
                         G_CALLBACK(dialog_response_cb), conn);
        g_signal_connect(conn->transfer_dialog, "delete-event",
                         G_CALLBACK(dialog_delete_cb), conn);
    }
    gtk_widget_show(conn->transfer_dialog);
    content = gtk_dialog_get_content_area(GTK_DIALOG(conn->transfer_dialog));
    gtk_container_set_border_width(GTK_CONTAINER(content), 12);

    widgets = transfer_task_widgets_new(task);
    g_hash_table_insert(conn->transfers, g_object_ref(task), widgets);
    gtk_box_pack_start(GTK_BOX(content),
                       widgets->vbox, TRUE, TRUE, 6);
}

static void new_file_transfer(SpiceMainChannel *main, SpiceFileTransferTask *task, gpointer user_data)
{
    spice_connection *conn = user_data;
    g_debug("new file transfer task");
    spice_connection_add_task(conn, task);
}

static void channel_new(SpiceSession *s, SpiceChannel *channel, gpointer data)
{
    spice_connection *conn = data;
    int id;

    g_object_get(channel, "channel-id", &id, NULL);
    SPICE_DEBUG("new channel (#%d)", id);

    if (SPICE_IS_MAIN_CHANNEL(channel)) {
        SPICE_DEBUG("new main channel");
        conn->main = SPICE_MAIN_CHANNEL(channel);
        g_signal_connect(channel, "channel-event",
                         G_CALLBACK(main_channel_event), conn);
        g_signal_connect(channel, "main-mouse-update",
                         G_CALLBACK(main_mouse_update), conn);
        g_signal_connect(channel, "main-agent-update",
                         G_CALLBACK(main_agent_update), conn);
        g_signal_connect(channel, "new-file-transfer",
                         G_CALLBACK(new_file_transfer), conn);
        main_mouse_update(channel, conn);
        main_agent_update(channel, conn);
    }

    if (SPICE_IS_DISPLAY_CHANNEL(channel)) {
        if (id >= SPICE_N_ELEMENTS(conn->wins))
            return;
        if (conn->wins[id] != NULL)
            return;
        SPICE_DEBUG("new display channel (#%d)", id);
        g_signal_connect(channel, "notify::monitors",
                         G_CALLBACK(display_monitors), conn);
        spice_channel_connect(channel);
    }

    if (SPICE_IS_INPUTS_CHANNEL(channel)) {
        SPICE_DEBUG("new inputs channel");
        g_signal_connect(channel, "inputs-modifiers",
                         G_CALLBACK(inputs_modifiers), conn);
    }

    if (SPICE_IS_PLAYBACK_CHANNEL(channel)) {
        SPICE_DEBUG("new audio channel");
        conn->audio = spice_audio_get(s, NULL);
    }

    if (SPICE_IS_USBREDIR_CHANNEL(channel)) {
        update_auto_usbredir_sensitive(conn);
    }

    if (SPICE_IS_PORT_CHANNEL(channel)) {
        g_signal_connect(channel, "notify::port-opened",
                         G_CALLBACK(port_opened), conn);
        g_signal_connect(channel, "port-data",
                         G_CALLBACK(port_data), conn);
        spice_channel_connect(channel);
    }
}

static void channel_destroy(SpiceSession *s, SpiceChannel *channel, gpointer data)
{
    spice_connection *conn = data;
    int id;

    g_object_get(channel, "channel-id", &id, NULL);
    if (SPICE_IS_MAIN_CHANNEL(channel)) {
        SPICE_DEBUG("zap main channel");
        conn->main = NULL;
    }

    if (SPICE_IS_DISPLAY_CHANNEL(channel)) {
        if (id >= SPICE_N_ELEMENTS(conn->wins))
            return;
        SPICE_DEBUG("zap display channel (#%d)", id);
        /* FIXME destroy widget only */
    }

    if (SPICE_IS_PLAYBACK_CHANNEL(channel)) {
        SPICE_DEBUG("zap audio channel");
    }

    if (SPICE_IS_USBREDIR_CHANNEL(channel)) {
        update_auto_usbredir_sensitive(conn);
    }

    if (SPICE_IS_PORT_CHANNEL(channel)) {
        if (SPICE_PORT_CHANNEL(channel) == stdin_port)
            stdin_port = NULL;
    }
}

static void migration_state(GObject *session,
                            GParamSpec *pspec, gpointer data)
{
    SpiceSessionMigration mig;

    g_object_get(session, "migration-state", &mig, NULL);
    if (mig == SPICE_SESSION_MIGRATION_SWITCHING)
        g_message("migrating session");
}


#ifdef USE_USBREDIR
/* ---- USB policy parsing ----
 *
 * Legacy --usb-policy:
 *   raw:<filter-string>
 *   block:printer,mass-storage,audio,camera,hid,smartcard
 *   allow:hid,audio
 *
 * Citrix-like policy:
 *   --usb-redirection=enabled|disabled
 *   --usb-existing-devices=deny|manual|connect
 *   --usb-new-devices=deny|manual|connect
 *   --usb-default-action=deny|allow|connect
 *   --usb-rule="DENY: class=hid"
 *   --usb-rule="ALLOW: class=printer"
 *   --usb-rule="CONNECT: vid=0x0951 pid=0x1666"
 *
 * DENY    -> blocked for manual and automatic redirection
 * ALLOW   -> manual redirection is allowed, automatic redirection is not
 * CONNECT -> manual redirection is allowed and automatic redirection is enabled
 */
typedef enum {
    USB_RULE_DENY = 0,
    USB_RULE_ALLOW,
    USB_RULE_CONNECT
} UsbPolicyAction;

static gboolean
usb_class_from_token(const gchar *tok, guint *klass)
{
    if (tok == NULL || *tok == '\0') {
        return FALSE;
    }

    if (g_ascii_strcasecmp(tok, "hid") == 0 || g_ascii_strcasecmp(tok, "input") == 0) {
        *klass = 0x03;
        return TRUE;
    }
    if (g_ascii_strcasecmp(tok, "printer") == 0) {
        *klass = 0x07;
        return TRUE;
    }
    if (g_ascii_strcasecmp(tok, "mass-storage") == 0 ||
        g_ascii_strcasecmp(tok, "storage") == 0 ||
        g_ascii_strcasecmp(tok, "flash") == 0) {
        *klass = 0x08;
        return TRUE;
    }
    if (g_ascii_strcasecmp(tok, "smartcard") == 0 ||
        g_ascii_strcasecmp(tok, "smart-card") == 0 ||
        g_ascii_strcasecmp(tok, "ccid") == 0) {
        *klass = 0x0b;
        return TRUE;
    }
    if (g_ascii_strcasecmp(tok, "video") == 0 ||
        g_ascii_strcasecmp(tok, "camera") == 0 ||
        g_ascii_strcasecmp(tok, "webcam") == 0) {
        *klass = 0x0e;
        return TRUE;
    }
    if (g_ascii_strcasecmp(tok, "audio") == 0) {
        *klass = 0x01;
        return TRUE;
    }

    if (g_str_has_prefix(tok, "0x") || g_ascii_isdigit(tok[0])) {
        gchar *end = NULL;
        guint64 v;

        v = g_ascii_strtoull(tok, &end, 0);
        if (end && *end == '\0' && v <= 0xff) {
            *klass = (guint)v;
            return TRUE;
        }
    }

    return FALSE;
}

static gboolean
parse_usb_mode(const gchar *value,
               UsbPolicyAction *out_action,
               GError **err)
{
    if (!value || !*value) {
        g_set_error(err, G_OPTION_ERROR, G_OPTION_ERROR_BAD_VALUE,
                    "USB mode must be deny, manual/allow or connect");
        return FALSE;
    }

    if (g_ascii_strcasecmp(value, "deny") == 0 ||
        g_ascii_strcasecmp(value, "disabled") == 0 ||
        g_ascii_strcasecmp(value, "block") == 0) {
        *out_action = USB_RULE_DENY;
        return TRUE;
    }

    if (g_ascii_strcasecmp(value, "manual") == 0 ||
        g_ascii_strcasecmp(value, "allow") == 0 ||
        g_ascii_strcasecmp(value, "enabled") == 0) {
        *out_action = USB_RULE_ALLOW;
        return TRUE;
    }

    if (g_ascii_strcasecmp(value, "connect") == 0 ||
        g_ascii_strcasecmp(value, "auto") == 0 ||
        g_ascii_strcasecmp(value, "redirect") == 0) {
        *out_action = USB_RULE_CONNECT;
        return TRUE;
    }

    g_set_error(err, G_OPTION_ERROR, G_OPTION_ERROR_BAD_VALUE,
                "Unknown USB mode '%s' (use deny, manual/allow or connect)", value);
    return FALSE;
}

static gint
usb_action_allow_for_policy(UsbPolicyAction action)
{
    return action == USB_RULE_DENY ? 0 : 1;
}

static gint
usb_action_allow_for_auto(UsbPolicyAction action)
{
    return action == USB_RULE_CONNECT ? 1 : 0;
}

static const gchar *
usb_rule_skip_spaces(const gchar *p)
{
    while (p && g_ascii_isspace(*p)) {
        p++;
    }
    return p;
}

static gboolean
usb_parse_rule_action(const gchar *rule,
                      UsbPolicyAction *action,
                      const gchar **rest,
                      GError **err)
{
    gchar *tmp;
    gchar *sep = NULL;
    gchar *action_name;
    gboolean ok;

    tmp = g_strdup(rule);
    sep = strchr(tmp, ':');
    if (!sep) {
        sep = strchr(tmp, ' ');
    }

    if (!sep) {
        g_set_error(err, G_OPTION_ERROR, G_OPTION_ERROR_BAD_VALUE,
                    "Invalid --usb-rule '%s' (expected ACTION: matchers)", rule);
        g_free(tmp);
        return FALSE;
    }

    *sep = '\0';
    action_name = g_strstrip(tmp);
    ok = parse_usb_mode(action_name, action, err);
    g_free(tmp);

    if (!ok) {
        return FALSE;
    }

    sep = strchr(rule, ':');
    if (!sep) {
        sep = strchr(rule, ' ');
    }

    *rest = usb_rule_skip_spaces(sep + 1);
    if (!*rest || !**rest) {
        g_set_error(err, G_OPTION_ERROR, G_OPTION_ERROR_BAD_VALUE,
                    "Invalid --usb-rule '%s' (empty matcher)", rule);
        return FALSE;
    }

    return TRUE;
}

static gboolean
usb_parse_match_number(const gchar *value, gint max, gint *out)
{
    gchar *end = NULL;
    guint64 v;

    if (!value || !*value) {
        return FALSE;
    }

    v = g_ascii_strtoull(value, &end, 0);
    if (!end || *end != '\0' || v > (guint64)max) {
        return FALSE;
    }

    *out = (gint)v;
    return TRUE;
}

static gboolean
usb_filter_tuple_from_rule(const gchar *rule,
                           UsbPolicyAction *action,
                           gint *klass,
                           gint *vid,
                           gint *pid,
                           gint *bcd,
                           GError **err)
{
    const gchar *matchers;
    gchar **parts = NULL;
    guint matched_fields = 0;
    int i;

    *klass = -1;
    *vid = -1;
    *pid = -1;
    *bcd = -1;

    if (!usb_parse_rule_action(rule, action, &matchers, err)) {
        return FALSE;
    }

    /* Compact compatibility: CONNECT:mass-storage */
    if (!strchr(matchers, '=') && !strchr(matchers, ',')) {
        guint cls;

        if (!usb_class_from_token(matchers, &cls)) {
            g_set_error(err, G_OPTION_ERROR, G_OPTION_ERROR_BAD_VALUE,
                        "Unknown USB class token '%s'", matchers);
            return FALSE;
        }

        *klass = (gint)cls;
        return TRUE;
    }

    parts = g_strsplit_set(matchers, ",; ", -1);
    for (i = 0; parts && parts[i]; i++) {
        gchar **kv = NULL;
        gchar *key;
        gchar *value;

        if (parts[i][0] == '\0') {
            continue;
        }

        kv = g_strsplit(parts[i], "=", 2);
        if (!kv || !kv[0] || !kv[1]) {
            g_strfreev(kv);
            g_set_error(err, G_OPTION_ERROR, G_OPTION_ERROR_BAD_VALUE,
                        "Invalid matcher '%s' in --usb-rule '%s'", parts[i], rule);
            g_strfreev(parts);
            return FALSE;
        }

        key = g_strstrip(kv[0]);
        value = g_strstrip(kv[1]);

        if (g_ascii_strcasecmp(key, "class") == 0 ||
            g_ascii_strcasecmp(key, "cls") == 0) {
            guint cls;

            if (!usb_class_from_token(value, &cls)) {
                g_set_error(err, G_OPTION_ERROR, G_OPTION_ERROR_BAD_VALUE,
                            "Unknown USB class token '%s'", value);
                g_strfreev(kv);
                g_strfreev(parts);
                return FALSE;
            }
            *klass = (gint)cls;
            matched_fields++;
        } else if (g_ascii_strcasecmp(key, "vid") == 0 ||
                   g_ascii_strcasecmp(key, "vendor") == 0 ||
                   g_ascii_strcasecmp(key, "vendor-id") == 0) {
            if (!usb_parse_match_number(value, 0xffff, vid)) {
                g_set_error(err, G_OPTION_ERROR, G_OPTION_ERROR_BAD_VALUE,
                            "Invalid USB VID '%s'", value);
                g_strfreev(kv);
                g_strfreev(parts);
                return FALSE;
            }
            matched_fields++;
        } else if (g_ascii_strcasecmp(key, "pid") == 0 ||
                   g_ascii_strcasecmp(key, "product") == 0 ||
                   g_ascii_strcasecmp(key, "product-id") == 0) {
            if (!usb_parse_match_number(value, 0xffff, pid)) {
                g_set_error(err, G_OPTION_ERROR, G_OPTION_ERROR_BAD_VALUE,
                            "Invalid USB PID '%s'", value);
                g_strfreev(kv);
                g_strfreev(parts);
                return FALSE;
            }
            matched_fields++;
        } else if (g_ascii_strcasecmp(key, "bcd") == 0 ||
                   g_ascii_strcasecmp(key, "version") == 0) {
            if (!usb_parse_match_number(value, 0xffff, bcd)) {
                g_set_error(err, G_OPTION_ERROR, G_OPTION_ERROR_BAD_VALUE,
                            "Invalid USB bcdDevice '%s'", value);
                g_strfreev(kv);
                g_strfreev(parts);
                return FALSE;
            }
            matched_fields++;
        } else {
            g_set_error(err, G_OPTION_ERROR, G_OPTION_ERROR_BAD_VALUE,
                        "Unknown USB matcher '%s'", key);
            g_strfreev(kv);
            g_strfreev(parts);
            return FALSE;
        }

        g_strfreev(kv);
    }

    g_strfreev(parts);

    if (matched_fields == 0) {
        g_set_error(err, G_OPTION_ERROR, G_OPTION_ERROR_BAD_VALUE,
                    "Rule '%s' does not contain any supported matcher", rule);
        return FALSE;
    }

    return TRUE;
}

static void
usb_filter_append_tuple(GString *s,
                        gint klass,
                        gint vid,
                        gint pid,
                        gint bcd,
                        gint allow)
{
    if (s->len) {
        g_string_append_c(s, '|');
    }

    g_string_append_printf(s, "%d,%d,%d,%d,%d",
                           klass, vid, pid, bcd, allow);
}

static gchar *
build_usb_filter_string(const gchar *policy, gboolean default_allow, GError **err)
{
    GString *s;
    gboolean allow_mode;
    gchar **tokens;
    int i;

    if (!policy || !*policy) {
        return NULL;
    }

    if (g_str_has_prefix(policy, "raw:")) {
        return g_strdup(policy + 4);
    }

    if (g_str_has_prefix(policy, "block:")) {
        allow_mode = FALSE;
        policy += strlen("block:");
    } else if (g_str_has_prefix(policy, "allow:")) {
        allow_mode = TRUE;
        policy += strlen("allow:");
    } else {
        g_set_error(err, G_OPTION_ERROR, G_OPTION_ERROR_BAD_VALUE,
                    "Expected raw:, block: or allow:");
        return NULL;
    }

    s = g_string_new(NULL);
    tokens = g_strsplit(policy, ",", -1);
    for (i = 0; tokens && tokens[i]; i++) {
        gchar *tok = g_strstrip(tokens[i]);

        if (!tok || !*tok) {
            continue;
        }

        guint cls = 0;
        if (!usb_class_from_token(tok, &cls)) {
            g_set_error(err, G_OPTION_ERROR, G_OPTION_ERROR_BAD_VALUE,
                        "Unknown USB class token '%s' (use printer,mass-storage,audio,camera,hid,smartcard or 0xNN)", tok);
            g_strfreev(tokens);
            g_string_free(s, TRUE);
            return NULL;
        }

        usb_filter_append_tuple(s, (gint)cls, -1, -1, -1, allow_mode ? 1 : 0);
    }
    g_strfreev(tokens);

    usb_filter_append_tuple(s, -1, -1, -1, -1, default_allow ? 1 : 0);

    return g_string_free(s, FALSE);
}

static gchar *
build_usb_manual_policy_filter(UsbPolicyAction default_action,
                               GError **err)
{
    GString *s;
    guint i;

    s = g_string_new(NULL);

    for (i = 0; usb_policy_rules && i < usb_policy_rules->len; i++) {
        const gchar *rule = g_ptr_array_index(usb_policy_rules, i);
        UsbPolicyAction action;
        gint klass, vid, pid, bcd;

        if (!usb_filter_tuple_from_rule(rule, &action, &klass, &vid, &pid, &bcd, err)) {
            g_string_free(s, TRUE);
            return NULL;
        }

        usb_filter_append_tuple(s, klass, vid, pid, bcd,
                                usb_action_allow_for_policy(action));
    }

    usb_filter_append_tuple(s, -1, -1, -1, -1,
                            usb_action_allow_for_policy(default_action));

    return g_string_free(s, FALSE);
}

static gint
usb_action_allow_for_auto_event(UsbPolicyAction rule_action,
                                UsbPolicyAction event_action)
{
    if (rule_action == USB_RULE_DENY) {
        return 0;
    }

    if (rule_action == USB_RULE_CONNECT) {
        return 1;
    }

    return event_action == USB_RULE_CONNECT ? 1 : 0;
}

static gchar *
build_usb_auto_policy_filter(UsbPolicyAction default_policy_action,
                             UsbPolicyAction event_action,
                             GError **err)
{
    GString *s;
    guint i;

    s = g_string_new(NULL);

    for (i = 0; usb_policy_rules && i < usb_policy_rules->len; i++) {
        const gchar *rule = g_ptr_array_index(usb_policy_rules, i);
        UsbPolicyAction action;
        gint klass, vid, pid, bcd;

        if (!usb_filter_tuple_from_rule(rule, &action, &klass, &vid, &pid, &bcd, err)) {
            g_string_free(s, TRUE);
            return NULL;
        }

        usb_filter_append_tuple(s, klass, vid, pid, bcd,
                                usb_action_allow_for_auto_event(action, event_action));
    }

    usb_filter_append_tuple(s, -1, -1, -1, -1,
                            default_policy_action != USB_RULE_DENY &&
                            event_action == USB_RULE_CONNECT ? 1 : 0);

    return g_string_free(s, FALSE);
}

static gboolean
usb_rule_option_cb(const gchar *option_name G_GNUC_UNUSED,
                   const gchar *value,
                   gpointer data G_GNUC_UNUSED,
                   GError **error)
{
    UsbPolicyAction action;
    gint klass, vid, pid, bcd;

    if (!value || !*value) {
        g_set_error(error, G_OPTION_ERROR, G_OPTION_ERROR_BAD_VALUE,
                    "--usb-rule requires a non-empty value");
        return FALSE;
    }

    if (!usb_filter_tuple_from_rule(value, &action, &klass, &vid, &pid, &bcd, error)) {
        return FALSE;
    }

    if (!usb_policy_rules) {
        usb_policy_rules = g_ptr_array_new_with_free_func(g_free);
    }

    g_ptr_array_add(usb_policy_rules, g_strdup(value));
    usb_policy_cli_active = TRUE;
    return TRUE;
}

static gboolean
usb_redirection_disabled(void)
{
    return usb_redirection &&
           (g_ascii_strcasecmp(usb_redirection, "disabled") == 0 ||
            g_ascii_strcasecmp(usb_redirection, "off") == 0 ||
            g_ascii_strcasecmp(usb_redirection, "false") == 0 ||
            g_ascii_strcasecmp(usb_redirection, "0") == 0);
}

static gboolean
usb_redirection_enabled_value(void)
{
    return usb_redirection == NULL ||
           g_ascii_strcasecmp(usb_redirection, "enabled") == 0 ||
           g_ascii_strcasecmp(usb_redirection, "on") == 0 ||
           g_ascii_strcasecmp(usb_redirection, "true") == 0 ||
           g_ascii_strcasecmp(usb_redirection, "1") == 0;
}

static void
apply_usb_policy_to_connection(spice_connection *conn)
{
    SpiceUsbDeviceManager *manager;
    GError *e = NULL;
    gboolean have_new_policy;
    gboolean auto_usbredir = FALSE;
    UsbPolicyAction default_action = USB_RULE_DENY;
    UsbPolicyAction existing_action = USB_RULE_ALLOW;
    UsbPolicyAction new_action = USB_RULE_ALLOW;
    gchar *manual_filter = NULL;
    gchar *new_filter = NULL;
    gchar *existing_filter = NULL;

    manager = spice_usb_device_manager_get(conn->session, NULL);
    if (!manager) {
        return;
    }

    have_new_policy = usb_redirection != NULL ||
                      usb_existing_devices != NULL ||
                      usb_new_devices != NULL ||
                      usb_default_action != NULL ||
                      (usb_policy_rules && usb_policy_rules->len > 0);

    if (!have_new_policy && (!usb_policy || !*usb_policy)) {
        return;
    }

    usb_policy_cli_active = TRUE;

    if (usb_redirection && !usb_redirection_enabled_value() &&
        !usb_redirection_disabled()) {
        g_printerr("Invalid --usb-redirection: %s (use enabled or disabled)\\n",
                   usb_redirection);
        exit(2);
    }

    if (usb_redirection_disabled()) {
        manual_filter = g_strdup("-1,-1,-1,-1,0");
        new_filter = g_strdup("-1,-1,-1,-1,0");
        existing_filter = g_strdup("-1,-1,-1,-1,0");
        auto_usbredir = FALSE;
    } else if (have_new_policy) {
        if (usb_default_action &&
            !parse_usb_mode(usb_default_action, &default_action, &e)) {
            g_printerr("Invalid --usb-default-action: %s\\n",
                       e ? e->message : "unknown error");
            g_clear_error(&e);
            exit(2);
        }

        if (usb_existing_devices &&
            !parse_usb_mode(usb_existing_devices, &existing_action, &e)) {
            g_printerr("Invalid --usb-existing-devices: %s\\n",
                       e ? e->message : "unknown error");
            g_clear_error(&e);
            exit(2);
        }

        if (usb_new_devices &&
            !parse_usb_mode(usb_new_devices, &new_action, &e)) {
            g_printerr("Invalid --usb-new-devices: %s\\n",
                       e ? e->message : "unknown error");
            g_clear_error(&e);
            exit(2);
        }

        manual_filter = build_usb_manual_policy_filter(default_action, &e);
        if (!manual_filter) {
            g_printerr("Invalid --usb-rule: %s\\n",
                       e ? e->message : "unknown error");
            g_clear_error(&e);
            exit(2);
        }

        new_filter = build_usb_auto_policy_filter(default_action, new_action, &e);
        if (!new_filter) {
            g_printerr("Invalid --usb-rule/--usb-new-devices: %s\\n",
                       e ? e->message : "unknown error");
            g_clear_error(&e);
            exit(2);
        }

        existing_filter = build_usb_auto_policy_filter(default_action, existing_action, &e);
        if (!existing_filter) {
            g_printerr("Invalid --usb-rule/--usb-existing-devices: %s\\n",
                       e ? e->message : "unknown error");
            g_clear_error(&e);
            exit(2);
        }

        auto_usbredir = (new_action == USB_RULE_CONNECT ||
                         existing_action == USB_RULE_CONNECT);
        if (usb_policy_rules && usb_policy_rules->len > 0) {
            guint i;

            for (i = 0; i < usb_policy_rules->len; i++) {
                const gchar *rule = g_ptr_array_index(usb_policy_rules, i);
                UsbPolicyAction action;
                const gchar *rest = NULL;

                if (usb_parse_rule_action(rule, &action, &rest, NULL) &&
                    action == USB_RULE_CONNECT) {
                    auto_usbredir = TRUE;
                    break;
                }
            }
        }
    } else {
        gboolean def_allow = TRUE;

        if (g_str_has_prefix(usb_policy, "allow:")) {
            def_allow = FALSE;
        }

        manual_filter = build_usb_filter_string(usb_policy, def_allow, &e);
        if (!manual_filter) {
            g_printerr("Invalid --usb-policy: %s\\n",
                       e ? e->message : "unknown error");
            g_clear_error(&e);
            exit(2);
        }

        new_filter = g_strdup(manual_filter);
        existing_filter = g_strdup("-1,-1,-1,-1,0");
        auto_usbredir = TRUE;
    }

    g_object_set(manager,
                 "policy-filter", manual_filter,
                 "auto-connect-filter", new_filter,
                 "redirect-on-connect", existing_filter,
                 NULL);
    g_object_set(conn->gtk_session, "auto-usbredir", auto_usbredir, NULL);

    SPICE_DEBUG("USB policy from CLI: manual=%s new=%s existing=%s auto-usbredir=%s",
                manual_filter ? manual_filter : "(null)",
                new_filter ? new_filter : "(null)",
                existing_filter ? existing_filter : "(null)",
                auto_usbredir ? "yes" : "no");

    g_free(manual_filter);
    g_free(new_filter);
    g_free(existing_filter);
}
#endif /* USE_USBREDIR */

static spice_connection *connection_new(void)
{
    spice_connection *conn;
    SpiceUsbDeviceManager *manager;

    conn = g_new0(spice_connection, 1);
    conn->session = spice_session_new();
    conn->gtk_session = spice_gtk_session_get(conn->session);
    g_signal_connect(conn->session, "channel-new",
                     G_CALLBACK(channel_new), conn);
    g_signal_connect(conn->session, "channel-destroy",
                     G_CALLBACK(channel_destroy), conn);
    g_signal_connect(conn->session, "notify::migration-state",
                     G_CALLBACK(migration_state), conn);
    g_signal_connect(conn->session, "disconnected",
                     G_CALLBACK(connection_destroy), conn);

    manager = spice_usb_device_manager_get(conn->session, NULL);
#ifdef USE_USBREDIR
    apply_usb_policy_to_connection(conn);
#endif
    if (manager) {
        g_signal_connect(manager, "auto-connect-failed",
                         G_CALLBACK(usb_connect_failed), NULL);
        g_signal_connect(manager, "device-error",
                         G_CALLBACK(usb_connect_failed), NULL);
    }

    conn->transfers = g_hash_table_new_full(g_direct_hash, g_direct_equal,
                                            g_object_unref,
                                            (GDestroyNotify)transfer_task_widgets_free);
    connections++;
    SPICE_DEBUG("%s (%d)", __FUNCTION__, connections);
    return conn;
}

static void connection_connect(spice_connection *conn)
{
    conn->disconnecting = false;
    spice_session_connect(conn->session);
}

static void connection_disconnect(spice_connection *conn)
{
    if (conn->disconnecting)
        return;
    conn->disconnecting = true;
    spice_session_disconnect(conn->session);
}

static void connection_destroy(SpiceSession *session,
                               spice_connection *conn)
{
    for (int i = 0; i < SPICE_N_ELEMENTS(conn->wins); i++) {
        destroy_spice_window(conn->wins[i]);
    }
    g_object_unref(conn->session);
    g_hash_table_unref(conn->transfers);
    g_free(conn);

    connections--;
    SPICE_DEBUG("%s (%d)", __FUNCTION__, connections);
    if (connections > 0) {
        return;
    }

    g_main_loop_quit(mainloop);
}

/* ------------------------------------------------------------------ */

static GOptionEntry cmd_entries[] = {
    {
        .long_name        = "full-screen",
        .short_name       = 'f',
        .arg              = G_OPTION_ARG_NONE,
        .arg_data         = &fullscreen,
        .description      = N_("Open in full screen mode"),
    },{
        .long_name        = "version",
        .arg              = G_OPTION_ARG_NONE,
        .arg_data         = &version,
        .description      = N_("Display version and quit"),
    },{
        .long_name        = "title",
        .arg              = G_OPTION_ARG_STRING,
        .arg_data         = &spicy_title,
        .description      = N_("Set the window title"),
        .arg_description  = N_("<title>"),
    },{
#ifdef USE_USBREDIR
        .long_name        = "usb-policy",
        .arg              = G_OPTION_ARG_STRING,
        .arg_data         = &usb_policy,
        .description      = N_("Legacy USB redirection policy. Use raw:<filter> or block:/allow: lists"),
        .arg_description  = N_("<raw:...|block:...|allow:...>"),
    },{
        .long_name        = "usb-redirection",
        .arg              = G_OPTION_ARG_STRING,
        .arg_data         = &usb_redirection,
        .description      = N_("USB redirection master switch: enabled or disabled"),
        .arg_description  = N_("enabled|disabled"),
    },{
        .long_name        = "usb-existing-devices",
        .arg              = G_OPTION_ARG_STRING,
        .arg_data         = &usb_existing_devices,
        .description      = N_("Default action for USB devices already present when the SPICE session connects"),
        .arg_description  = N_("deny|manual|connect"),
    },{
        .long_name        = "usb-new-devices",
        .arg              = G_OPTION_ARG_STRING,
        .arg_data         = &usb_new_devices,
        .description      = N_("Default action for newly plugged USB devices"),
        .arg_description  = N_("deny|manual|connect"),
    },{
        .long_name        = "usb-default-action",
        .arg              = G_OPTION_ARG_STRING,
        .arg_data         = &usb_default_action,
        .description      = N_("Default action for devices not matched by --usb-rule"),
        .arg_description  = N_("deny|allow|connect"),
    },{
        .long_name        = "usb-rule",
        .arg              = G_OPTION_ARG_CALLBACK,
        .arg_data         = usb_rule_option_cb,
        .description      = N_("USB policy rule: DENY/ALLOW/CONNECT with class, vid, pid and/or bcd matchers"),
        .arg_description  = N_("ACTION: class=mass-storage|vid=0x1234 pid=0x5678"),
    },{
#endif
        /* end of list */
    }
};

static void usb_connect_failed(GObject               *object,
                               SpiceUsbDevice        *device,
                               GError                *error,
                               gpointer               data)
{
    GtkWidget *dialog;

    if (error->domain == G_IO_ERROR && error->code == G_IO_ERROR_CANCELLED)
        return;

    dialog = gtk_message_dialog_new(NULL, GTK_DIALOG_MODAL, GTK_MESSAGE_ERROR,
                                    GTK_BUTTONS_CLOSE,
                                    _("USB redirection error"));
    gtk_message_dialog_format_secondary_text(GTK_MESSAGE_DIALOG(dialog),
                                             "%s", error->message);
    gtk_dialog_run(GTK_DIALOG(dialog));
    gtk_widget_destroy(dialog);
}

static void setup_terminal(gboolean reset)
{
    int stdinfd = fileno(stdin);

    if (!isatty(stdinfd))
        return;

#ifdef HAVE_TERMIOS_H
    struct termios tios;
    static struct termios saved_tios;
    static bool saved = false;

    if (reset) {
        if (!saved)
            return;
        tios = saved_tios;
    } else {
        tcgetattr(stdinfd, &tios);
        saved_tios = tios;
        saved = true;
        tios.c_lflag &= ~(ICANON | ECHO);
    }

    tcsetattr(stdinfd, TCSANOW, &tios);
#endif
}

static void watch_stdin(void)
{
    int stdinfd = fileno(stdin);
    GIOChannel *gin;

    setup_terminal(false);
    gin = g_io_channel_unix_new(stdinfd);
    g_io_channel_set_flags(gin, G_IO_FLAG_NONBLOCK, NULL);
    g_io_add_watch(gin, G_IO_IN|G_IO_ERR|G_IO_HUP|G_IO_NVAL, input_cb, NULL);
}

int main(int argc, char *argv[])
{
    GError *error = NULL;
    GOptionContext *context;
    spice_connection *conn;
    gchar *conf_file, *conf;
    char *host = NULL, *port = NULL, *tls_port = NULL, *unix_path = NULL;

    keyfile = g_key_file_new();

    int mode = S_IRWXU;
    conf_file = g_build_filename(g_get_user_config_dir(), "spicy", NULL);
    if (g_mkdir_with_parents(conf_file, mode) == -1)
        SPICE_DEBUG("failed to create config directory");
    g_free(conf_file);

    conf_file = g_build_filename(g_get_user_config_dir(), "spicy", "settings", NULL);
    if (!g_key_file_load_from_file(keyfile, conf_file,
                                   G_KEY_FILE_KEEP_COMMENTS|G_KEY_FILE_KEEP_TRANSLATIONS, &error)) {
        SPICE_DEBUG("Couldn't load configuration: %s", error->message);
        g_clear_error(&error);
    }

    /* i18n */
    init_i18n();
    g_log_set_writer_func(spicy_log_writer, NULL, NULL);

    /* parse opts */
    gtk_init(&argc, &argv);
    gtk_window_set_default_icon_name("spicy");
    context = g_option_context_new(_("- spice client test application"));
    g_option_context_set_summary(context, _("Gtk+ test client to connect to Spice servers."));
    g_option_context_set_description(context, _("Report bugs to " PACKAGE_BUGREPORT "."));
    g_option_context_add_group(context, spice_get_option_group());
    g_option_context_set_main_group(context, spice_cmdline_get_option_group());
    g_option_context_add_main_entries(context, cmd_entries, GETTEXT_PACKAGE);
    g_option_context_add_group(context, gtk_get_option_group(TRUE));
    g_option_context_add_group(context, gst_init_get_option_group());
    if (!g_option_context_parse (context, &argc, &argv, &error)) {
        g_print(_("option parsing failed: %s\n"), error->message);
        exit(1);
    }
    g_option_context_free(context);

#ifdef USE_USBREDIR
    if (usb_policy || usb_redirection || usb_existing_devices ||
        usb_new_devices || usb_default_action ||
        (usb_policy_rules && usb_policy_rules->len > 0)) {
        usb_policy_cli_active = TRUE;
    }
#endif

    if (version) {
        g_print(_("spicy " PACKAGE_VERSION "\n"));
        exit(0);
    }

    mainloop = g_main_loop_new(NULL, false);

    conn = connection_new();
    spice_set_session_option(conn->session);
    spice_cmdline_session_setup(conn->session);

    g_object_get(conn->session,
                 "unix-path", &unix_path,
                 "host", &host,
                 "port", &port,
                 "tls-port", &tls_port,
                 NULL);
    /* If user doesn't provide hostname and port, show the dialog window
       instead of connecting to server automatically */
    if ((host == NULL || (port == NULL && tls_port == NULL)) && unix_path == NULL) {
        if (!spicy_connect_dialog(conn->session)) {
            exit(0);
        }
    }
    g_free(host);
    g_free(port);
    g_free(tls_port);
    g_free(unix_path);

    connection_connect(conn);
    if (connections > 0)
        g_main_loop_run(mainloop);
    g_main_loop_unref(mainloop);

    if ((conf = g_key_file_to_data(keyfile, NULL, &error)) == NULL ||
        !g_file_set_contents(conf_file, conf, -1, &error)) {
        SPICE_DEBUG("Couldn't save configuration: %s", error->message);
        g_error_free(error);
        error = NULL;
    }

    g_free(conf_file);
    g_free(conf);
    g_key_file_free(keyfile);

    g_free(spicy_title);
#ifdef USE_USBREDIR
    g_free(usb_policy);
    g_free(usb_redirection);
    g_free(usb_existing_devices);
    g_free(usb_new_devices);
    g_free(usb_default_action);
    if (usb_policy_rules) {
        g_ptr_array_unref(usb_policy_rules);
    }
#endif

    setup_terminal(true);
    gst_deinit();
    return 0;
}


