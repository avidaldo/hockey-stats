from django.urls import path

from webui import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("roster/", views.roster, name="roster"),
    path("roster/<int:player_id>/edit/", views.edit_player, name="edit-player"),
    path("roster/<int:player_id>/remove/", views.remove_player, name="remove-player"),
    path("games/new/", views.new_game, name="new-game"),
    path("games/correct/", views.correction_picker, name="correction-picker"),
    path("games/<int:game_id>/edit/", views.edit_game, name="edit-game"),
    path("mailing/", views.mailing, name="mailing"),
    path("mailing/<int:recipient_id>/remove/", views.remove_recipient, name="remove-recipient"),
]
