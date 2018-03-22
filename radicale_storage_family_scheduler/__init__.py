import os

import vobject
from radicale.storage import Collection as BaseCollection, path_to_filesystem

class Collection(BaseCollection):
    
    def _plugin_started(self):
        self.logger.debug("------------------")
        self.logger.debug("Plugin started.")
    
    def _plugin_finished(self):
        self.logger.debug("Plugin finished.")
        self.logger.debug("------------------")

    def _get_current_user(self):
        # HACK to get current user
        return self._filesystem_path.split("/")[-2]
        
    def _get_default_calendar_for_user(self, user, href):
        default_calendar_path = '.Radicale.private'
        dest_user = os.path.join(self._get_collection_root_folder(), user)
        if default_calendar_path not in os.listdir(dest_user):
            self.logger.error("No default (private) calendar found for user '%s'", user)
            self.logger.error("For this plugin to function properly, it is necessary to symlink one of the calendars as '%s'.", default_calendar_path)
            default_calendar_path = os.listdir(dest_user)[0] #TODO: could be adressbook???!!!
            self.logger.error("Using first collection found for this user as a workaround: %s", default_calendar_path)
        return os.path.join(dest_user, default_calendar_path, href)
    
    def _get_user_from_attendee(self, attendee):
        return attendee.value.replace("mailto:", "")
    
    def _get_family(self):
        root_folder = self._get_collection_root_folder()
        return [ name for name in os.listdir(root_folder) if os.path.isdir(os.path.join(root_folder, name)) ]
        
    def _get_family_members(self, attendees):
        current_user = self._get_current_user()
        
        family_members = []
        for attendee in attendees:
            user = self._get_user_from_attendee(attendee)
            family = self._get_family()
            
            if user == current_user:
                self.logger.debug("Attendee with mail adress '%s' is the currently logged in user.", user)
            elif user not in family:
                self.logger.debug("Attendee with mail adress '%s' is NOT a member of the family: %s", user, family)
                self.logger.debug("Please note that Radicale will not send any notification e-mails!")
            else:
                self.logger.debug("Attendee with mail adress '%s' IS member of the family: %s", user, family)
                family_members.append(attendee)
        return family_members
    
    def _is_symlink(self, href):
        path = path_to_filesystem(self._filesystem_path, href)
        return os.path.islink(path)
    
    def _is_update(self, href):
        path = path_to_filesystem(self._filesystem_path, href)
        return os.path.isfile(path)
    
    def _check_for_calendar_object(self, vobject_item):
        is_calendar = vobject_item.name == "VCALENDAR"
        if not is_calendar:
            self.logger.debug("vObject is not vCalendar, continuing with standard storage.")
            self._plugin_finished()
        return is_calendar
        
    def _get_attendees(self, vobject_item):
        try:
            return vobject_item.vevent.attendee_list #TODO: likely to get error with whole calendars!
        except AttributeError:
            return None

    def _get_real_collection(self, href):
        path = path_to_filesystem(self._filesystem_path, href)
        real = os.path.realpath(path).replace(self._get_collection_root_folder() + "/", "").replace("/" + href, "")
        return next(self.discover(real), None)
    
    def delete(self, href=None):
        self._plugin_started()
        
        current_user = self._get_current_user()
        item = self.get(href)
        vobject_item = item.item
        
        if not self._check_for_calendar_object(vobject_item):
            super().delete(href)
            return
        
        #for deleting the whole collection
        #TODO: if deleting whole collection, problem with events symlinked to the collection!
        if href is None:
            self.logger.debug("DELETE action on whole collection.")
            self.logger.debug("Up to now, this plugin is not able to handle this case properly.")
            self._plugin_finished()
            super().delete()
            return
        
        #check for symlinks
        if self._is_symlink(href):
            self.logger.debug("DELETE action on symlinked event.")
            self.logger.debug("The plugin will behave as following:")
            self.logger.debug("Delete the current user from the attendees list and remove the symlink for the current user.")
            collection = self._get_real_collection(href)
            item = collection.get(href)
            try:
                vobject_item.vevent.attendee_list = [attendee for attendee in vobject_item.vevent.attendee_list if self._get_user_from_attendee(attendee) != current_user]
                collection = self._get_real_collection(href)
                item = collection.upload(href, vobject_item)
                
                path = path_to_filesystem(self._filesystem_path, item.href)
                self.logger.debug("Path: " + path)
                        
                os.unlink(path)
                
                # Track the change
                self._update_history_etag(href, None)
                self._clean_history_cache()
                
                self._plugin_finished()
                return
            except:
                self.logger.error("Plugin encountered an error while trying to delete attendees and/or symbolic links for family members.")
                self.logger.error(e)

        attendees = self._get_attendees(vobject_item)
        if not attendees:
            self.logger.debug("No attendees found in %s, continuing with standard storage.", href)
            self._plugin_finished()
            super().delete(href)
            return
        
        self.logger.debug("%i attendees found in %s.", len(attendees), href)
        
        for family_member in self._get_family_members(attendees):
            try:
                user = self._get_user_from_attendee(family_member)
                
                self.logger.debug("Deleting symbolic link to delete event for %s too.", user)
                dest = self._get_default_calendar_for_user(user, href)
                self.logger.debug("Path: " + dest)
                
                os.unlink(dest)
                
                # Track the change
                self._update_history_etag(href, None)
                self._clean_history_cache()
            except:
                self.logger.error("Plugin encountered an error while trying to delete symbolic links for family members.")
                self.logger.error(e)
        
        self._plugin_finished()
        super().delete(href)
    
    def move(self, item, to_collection, to_href):
        raise NotImplementedError()
        super().move(href)

    def upload(self, href, vobject_item):
        item = None
        
        self._plugin_started()
        
        if not self._check_for_calendar_object(vobject_item):
            return super().upload(href, vobject_item)
        
        #check for symlinks
        if self._is_symlink(href):
            self.logger.debug("PUT action on symlinked event.")
            self.logger.debug("Continue with the real path of the event.")
            collection = self._get_real_collection(href)
            self._plugin_finished()
            item = collection.upload(href, vobject_item)
            # Track the change
            self._update_history_etag(href, item)
            self._clean_history_cache()
            return item            
        
        if self._is_update(href):
            self.logger.debug("PUT action to update an existing event.")
            vobject_item_old = self.get(href).item
            attendees_old = self._get_attendees(vobject_item_old)
            if not attendees_old:
                self.logger.debug("No attendees found in the old version on disk.")
            else:
                self.logger.debug("%i attendees found in the old version on disk.", len(attendees_old))
                users_old = [ self._get_user_from_attendee(family_member) for family_member in self._get_family_members(attendees_old) ]
                self.logger.debug("Removing all the symlinks for the attendees of the old version (will be added later again if needed).")
                for user_old in users_old:
                    dest = self._get_default_calendar_for_user(user_old, href)
                    self.logger.debug("Path: " + dest)
                    os.unlink(dest)
        
        attendees = self._get_attendees(vobject_item)
        if not attendees:
            self.logger.debug("No attendees found in %s, continuing with standard storage.", href)
            self._plugin_finished()
            return super().upload(href, vobject_item)
        
        self.logger.debug("%i attendees found in %s.", len(attendees), href)
        
        for family_member in self._get_family_members(attendees):
            try:
                user = self._get_user_from_attendee(family_member)
                
                try:
                    family_member.partstat_param
                except:
                    family_member.partstat_param = "NEEDS-ACTION"
                
                if family_member.partstat_param == "ACCEPTED":
                    self.logger.debug("PARTSTAT is already set to ACCEPTED.")
                elif family_member.partstat_param == "NEEDS-ACTION":
                    family_member.partstat_param = "ACCEPTED"
                    self.logger.debug("Set PARTSTAT automatically to ACCEPTED.")
                
                self.logger.debug("Creating a symbolic link to make event accessible for %s.", user)
                src = path_to_filesystem(self._filesystem_path, href)
                dest = self._get_default_calendar_for_user(user, href)
                self.logger.debug("Source: " + src)
                self.logger.debug("Destination: " + dest)
                
                os.symlink(src, dest)
                
                real = os.path.realpath(dest.replace("/" + href, "")).replace(self._get_collection_root_folder() + "/", "")
                collection = next(self.discover(real))
                
                # Track the change
                collection._update_history_etag(href, item)
                collection._clean_history_cache()
            except Exception as e:
                self.logger.error("Plugin encountered an error while trying to auto-accept and/or link for family members.")
                self.logger.error(e)

        self._plugin_finished()        
        return super().upload(href, vobject_item)
