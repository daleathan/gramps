#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2007  B. Malengier
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

"""
Display a person's relations to the home person
"""
#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------

from Simple import SimpleAccess, SimpleDoc
from gettext import gettext as _
from PluginUtils import register_quick_report
from ReportBase import CATEGORY_QR_PERSON

from PluginUtils import Tool, relationship_class, register_tool

# define the formatting string once as a constant. Since this is reused

__FMT      = "%-3d %s"
__FMT_VOID = "    %s"
__FMT_DET1 = "%-3s %-15s"
__FMT_DET2 = "%-30s %-15s\t%-10s %-2s"

    
def run(database, document, person):
    """
    Obtains all relationships, displays the relations, and in details, the 
    relation path
    """
    
    sdb = SimpleAccess(database)
    sdoc = SimpleDoc(document)
    rel_class = relationship_class()

    #get home_person
    home_person = database.get_default_person()
    if not home_person :
        sdoc.paragraph(_("Home person not set."))
        return

    #print title
    p2 = sdb.name(home_person)
    p1 = sdb.name(person)
    sdoc.title(_("Relationships of %s to %s") % (p1 ,p2))
    sdoc.paragraph("")
    
    if person.handle == home_person.handle :
        sdoc.paragraph(__FMT_VOID % (_("%s and %s are the same person.") % (
                                            p1, p2)) )
        return
    
    #obtain all relationships, assume home person has largest tree
    common, msg_list = rel_class.get_relationship_distance_new(
                database, person, home_person,
                all_families=True, 
                all_dist=True, 
                only_birth=False,
                max_depth=20)
                
    #check if not a family too:
    is_spouse = rel_class.is_spouse(database,person,home_person)
    if is_spouse:
        rel_string = is_spouse
        rstr = _("%(person)s is the %(relationship)s of %(active_person)s."
                     ) % {'person' : p2, 'relationship' : rel_string,
                          'active_person' : p1 }
        sdoc.paragraph(__FMT_VOID % (rstr))
        sdoc.paragraph("")
    
    #all relations
    if (not common or common[0][0]== -1 ) and not is_spouse:
        rstr = _("%(person)s and %(active_person)s are not related.") % {
                'person' : p2, 'active_person' : p1 }
        sdoc.paragraph(__FMT_VOID % (rstr))
        sdoc.paragraph("")
        
    if not common or common[0][0]== -1 :
        remarks(msg_list,sdoc)
        return
    
    count = 1

    #collapse common so parents of same fam in common are one line
    commonnew = rel_class.collapse_relations(common)

    for relation in commonnew: 
        birth = rel_class.only_birth(relation[2])\
                    and rel_class.only_birth(relation[4])
        rel_str = rel_class.get_single_relationship_string(
                                len(relation[4]), len(relation[2]), 
                                home_person.get_gender(), person.get_gender(),
                                relation[4], relation[2], 
                                only_birth = birth)
        sdoc.paragraph(__FMT % (count, rel_str))
        count += 1
            
    remarks(msg_list, sdoc)
    
    sdoc.paragraph("")
    sdoc.header1(_("Detailed path from %(person)s to common ancestor") % {'person':p1})
    sdoc.paragraph("")
    sdoc.header2(__FMT_DET1 % (_('   '), _('Name Common ancestor')))
    sdoc.header2(__FMT_DET2 % (' ', _('Parent'), _('Birth'), _('Family')))
    sdoc.paragraph("")
    count = 1
    for relation in commonnew: 
        counter = str(count)
        name = _('Unknown')
        if relation[1]:
            name = sdb.name(database.get_person_from_handle(relation[1][0]))
            for handle in relation[1][1:]:
                name += ' ' + _('and') + ' ' + \
                        sdb.name(database.get_person_from_handle(handle))
        sdoc.paragraph(__FMT_DET1 % (counter, name))
        for rel,fam in zip(relation[2],relation[3]) :
            par_str = _('Unknown') #when sibling, parent is unknown
            if rel == rel_class.REL_MOTHER \
                    or rel == rel_class.REL_MOTHER_NOTBIRTH:
                par_str = _('Mother')
            if rel == rel_class.REL_FATHER \
                    or rel == rel_class.REL_FATHER_NOTBIRTH:
                par_str = _('Father')
            if (rel == rel_class.REL_FAM_BIRTH 
                    or rel == rel_class.REL_FAM_NONBIRTH 
                    or rel == rel_class.REL_FAM_BIRTH_MOTH_ONLY
                    or rel == rel_class.REL_FAM_BIRTH_FATH_ONLY):
                par_str = _('Parents')
            birth_str = _('Yes')
            if (rel == rel_class.REL_MOTHER_NOTBIRTH 
                    or rel == rel_class.REL_FATHER_NOTBIRTH 
                    or rel == rel_class.REL_FAM_NONBIRTH):
                birth_str = _('No')
            elif (rel == rel_class.REL_FAM_BIRTH_FATH_ONLY 
                    or rel == rel_class.REL_FAM_BIRTH_MOTH_ONLY):
                birth_str = _('Partial')
            sdoc.paragraph(__FMT_DET2 % (' ', par_str, birth_str, str(fam+1)))
            counter=''
            name = ''
        count += 1
    
    sdoc.paragraph("")
    sdoc.header1(_("Detailed path from %(person)s to common ancestor") % {'person':p2})
    sdoc.paragraph("")
    sdoc.header2(__FMT_DET1 % (_('   '), _('Name Common ancestor')))
    sdoc.header2(__FMT_DET2 % (' ', _('Parent'), _('Birth'), _('Family')))
    sdoc.paragraph("")
    count = 1
    for relation in commonnew: 
        counter = str(count)
        name = _('Unknown')
        if relation[1]:
            name = sdb.name(database.get_person_from_handle(relation[1][0]))
            for handle in relation[1][1:]:
                name += ' ' + _('and') + ' ' + \
                        sdb.name(database.get_person_from_handle(handle))
        sdoc.paragraph(__FMT_DET1 % (counter, name))
        for rel,fam in zip(relation[4],relation[5]) :
            par_str = _('Unknown')
            if rel == rel_class.REL_MOTHER \
                    or rel == rel_class.REL_MOTHER_NOTBIRTH:
                par_str = _('Mother')
            if rel == rel_class.REL_FATHER \
                    or rel == rel_class.REL_FATHER_NOTBIRTH:
                par_str = _('Father')
            if (rel == rel_class.REL_FAM_BIRTH 
                    or rel == rel_class.REL_FAM_NONBIRTH 
                    or rel == rel_class.REL_FAM_BIRTH_MOTH_ONLY
                    or rel == rel_class.REL_FAM_BIRTH_FATH_ONLY):
                par_str = _('Parents')
            birth_str = _('Yes')
            if (rel == rel_class.REL_MOTHER_NOTBIRTH 
                    or rel == rel_class.REL_FATHER_NOTBIRTH 
                    or rel == rel_class.REL_FAM_NONBIRTH):
                birth_str = _('No')
            elif (rel == rel_class.REL_FAM_BIRTH_FATH_ONLY 
                    or rel == rel_class.REL_FAM_BIRTH_MOTH_ONLY):
                birth_str = _('Partial')
            sdoc.paragraph(__FMT_DET2 % (' ', par_str, birth_str, str(fam+1)))
            counter=''
            name = ''
        count += 1
    
            
def remarks(msg_list,sdoc):
    if msg_list :
        sdoc.paragraph("")
        sdoc.header1(_("Remarks"))
        sdoc.paragraph("")
        sdoc.paragraph(_("The following problems where encountered:"))
        for msg in msg_list :
            sdoc.paragraph(msg)
        sdoc.paragraph("")
        sdoc.paragraph("")
        

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
register_quick_report(
    name = 'all_relations',
    category = CATEGORY_QR_PERSON,
    run_func = run,
    translated_name = _("Relation to Home Person"),
    status = _("Stable"),
    description= _("Display all relationships between person and home person."),
    author_name="B. Malengier",
    author_email="benny.malengier@gramps-project.org"
    )
