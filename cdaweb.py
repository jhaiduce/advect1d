import urllib2
import xml.etree.ElementTree as ET

cdaweb_base_url='https://cdaweb.gsfc.nasa.gov/WS/cdasr/1'

def fetch_xml(url):
    """
    Fetch a URL and parse it as XML using ElementTree
    """
    resp=urllib2.urlopen(url)
    tree=ET.parse(resp)
    return tree

def element_to_dict(element):
    """
    Convert an ElementTree element into a dictionary
    """

    # Dictionary to represent the element and its children
    elem_dict={}
    for child in element:
        # Separate the schema name from the tag name
        tagname=child.tag.split('}')[1]

        if child.text is not None:
            # If the child is a text object, use it as-is
            child_value=child.text
        else:
            # Child is an XML element, parse it
            child_value=element_to_dict(child)

        # Add child to the dictionary
        if tagname in elem_dict.keys():
            # Tag is already in the dictionary, make a list instead
            try:
                elem_dict[tagname].append(child_value)
            except AttributeError:
                # Existing key is a scalar, convert it to a list and add
                # the new value to the end
                elem_dict[tagname]=[elem_dict[tagname],child_value]
        else:
            elem_dict[tagname]=child_value
    return elem_dict

def xml_to_dict(tree):
    """
    Convert an ElementTree tree to a dictionary
    """
    root=tree.getroot()
    dicts=[]
    for element in root:
        dicts.append(element_to_dict(element))
    return dicts

def get_dataviews():
    """
    Get all the CDAWeb dataviews
    """
    return xml_to_dict(fetch_xml(cdaweb_base_url+'/dataviews'))

def get_observatories(dataview):
    """
    Get a list of observatories in a dataview
    """
    return xml_to_dict(fetch_xml(cdaweb_base_url+'/dataviews/'+dataview+'/observatoryGroups'))

def get_datasets(dataview,observatoryGroup=None):
    """
    Get a list of datasets in a dataview (optionally filtered by an 
    observatory group)

    Example:

    get_datasets('sp_phys')

    """
    getdata={}
    if observatoryGroup is not None:
        getdata['observatoryGroup']=observatoryGroup

    getstr=''
    for key,value in getdata.iteritems():
        getstr+= key+'='+value
    return xml_to_dict(fetch_xml(cdaweb_base_url+'/dataviews/'+dataview+'/datasets?'+getstr))

def get_dataset_variables(dataview,dataset):
    """
    Get the variables in a dataset

    Example:

    get_dataset_variables('sp_phys','OMNI2_H0_MRG1HR')

    """
    return xml_to_dict(fetch_xml(cdaweb_base_url+'/dataviews/'+dataview+'/datasets/'+dataset+'/variables'))

def get_dataset_inventory(dataview,dataset):
    """
    Get the inventory (available time ranges) for a dataset

    Example:

    get_dataset_inventory('sp_phys','OMNI2_H0_MRG1HR')

    """
    return xml_to_dict(fetch_xml(cdaweb_base_url+'/dataviews/'+dataview+'/datasets/'+dataset+'/inventory'))

def datetime_to_cdaweb_url_format(datetime_value):
    """
    Convert a python datetime into a string formatted the way CDAWeb expects
    """
    from datetime import datetime 

    return '{0:%Y}{0:%m}{0:%d}T{0:%H}{0:%M}{0:%S}Z'.format(datetime_value)

def get_file(dataview,dataset,start_date,end_date,variables,format='cdf'):
    """
    Get a data file from CDAWeb

    dataview (str): A CDAWeb dataview
    dataset (str): A CDAWeb dataset
    start_date (datetime): Start date/time for the request
    end_date (datetime): End date/time for the request
    variables (sequence of strings): What variables to include
    format (str): What file format to retrieve (cdf, text, or gif)

    Example:

    from datetime import datetime
    get_file('sp_phys','OMNI2_H0_MRG1HR',datetime(2005,1,1),datetime(2005,2,1),['KP1800'])

    """

    start_date_str=datetime_to_cdaweb_url_format(start_date)
    end_date_str=datetime_to_cdaweb_url_format(end_date)

    if isinstance(variables,basestring):
        variables=(variables,)

    url=cdaweb_base_url+'/dataviews/'+dataview+'/datasets/'+dataset+'/data/'+start_date_str+','+end_date_str+'/'+','.join(variables)+'?format='+format
    print url

    root=fetch_xml(url).getroot()

    file_url=root.findtext('cda:FileDescription/cda:Name',namespaces={'cda':'http://cdaweb.gsfc.nasa.gov/schema'})
    
    if file_url is None:
        status=root.findtext('cda:Status',namespaces={'cda':'http://cdaweb.gsfc.nasa.gov/schema'})
        error=root.findtext('cda:Error',namespaces={'cda':'http://cdaweb.gsfc.nasa.gov/schema'})
        if status is not None:
            raise ValueError(status)
        elif error is not None:
            raise ValueError(error)

    data_response=urllib2.urlopen(file_url)

    return data_response

def get_cdf(*args,**kwargs):
    """
    Get a CDF file and read it (all arguments are passed to cdaweb.get_file)

    Example:

    from datetime import datetime
    get_cdf('sp_phys','OMNI2_H0_MRG1HR',datetime(2005,1,1),datetime(2005,2,1),['KP1800'])

    """

    resp=get_file(*args,**kwargs)

    from tempfile import NamedTemporaryFile
    from shutil import copyfileobj
    import spacepy.datamodel as dm

    with NamedTemporaryFile() as tmpfile:
        copyfileobj(resp,tmpfile)
        tmpfile.seek(0)
        data=dm.fromCDF(tmpfile.name)

    return data
