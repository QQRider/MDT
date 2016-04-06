import glob
import logging
import os
import shutil
from six import string_types
from mdt import protocols
from mdt.components_loader import BatchProfilesLoader
from mdt.data_loaders.protocol import ProtocolLoader
from mdt.masking import create_write_median_otsu_brain_mask
from mdt.protocols import load_protocol, load_bvec_bval
from mdt.utils import split_image_path, AutoDict

__author__ = 'Robbert Harms'
__date__ = "2015-08-21"
__maintainer__ = "Robbert Harms"
__email__ = "robbert.harms@maastrichtuniversity.nl"


class BatchProfile(object):

    def __init__(self):
        """Instantiate this BatchProfile
        """
        self._root_dir = ''

    def set_root_dir(self, root_dir):
        """Set the root dir. That is, the directory we search in for batch fit subjects.

        Args:
            root_dir (str): the root dir to use
        """
        self._root_dir = root_dir

    def get_root_dir(self):
        """Get the root dir this profile uses.

        Returns:
            str: the root dir this batch profile uses.
        """
        return self._root_dir

    def get_models_to_fit(self):
        """Get the list of models we want to fit to every found subject.

        The models can either be real model objects, or strings with the model names.

        Returns:
            list: the list of models we want to fit to the subjects
        """

    def get_model_protocol_options(self):
        """Get the protocol options we would like to use.

        These protocol options define per model which shells to use from the data. These are merged with the
        model protocol options defined in the protocol.

        Returns:
            dict: configuration dictionary
        """

    def get_subjects(self):
        """Get the information about all the subjects in the current folder.

        Returns:
            list of SubjectInfo: the information about the found subjects
        """

    def profile_suitable(self):
        """Check if this directory can be used to load subjects from using this batch fitting profile.

        This is used for auto detecting the best batch fitting profile to use for loading
        subjects from the given root dir.

        Returns:
            boolean: true if this batch fitting profile can load datasets from this root directory, false otherwise.
        """

    def get_subjects_count(self):
        """Get the number of subjects this batch fitting profile can load from the current root directory.

        Returns:
            int: the number of subjects this batch fitting profile can load from the given directory.
        """


class SimpleBatchProfile(BatchProfile):

    def __init__(self):
        """A base class for quickly implementing a batch profile.

        Implementing classes need only implement the method _get_subjects(). This class will handle the rest.

        Attributes:
            output_base_dir (str): the standard subject output dir, defaults to 'output'
            output_sub_dir (str): if given, a sub directory (in the default output dir) to place the output in
            models_to_fit (list): list of model names or model objects to use during fitting
        """
        super(SimpleBatchProfile, self).__init__()
        self._subjects_found = None
        self._output_base_dir = 'output'
        self._output_sub_dir = None
        self.models_to_fit = ('BallStick (Cascade)',
                              'Tensor (Cascade)',
                              'Noddi (Cascade)',
                              'BallStickStickStick (Cascade)',
                              'Charmed_r1 (Cascade)',
                              'Charmed_r2 (Cascade)',
                              'Charmed (Cascade)')

    @property
    def output_base_dir(self):
        return self._output_base_dir

    @output_base_dir.setter
    def output_base_dir(self, output_base_dir):
        self._output_base_dir = output_base_dir
        self._subjects_found = None

    @property
    def output_sub_dir(self):
        return self._output_sub_dir

    @output_sub_dir.setter
    def output_sub_dir(self, output_sub_dir):
        self._output_sub_dir = output_sub_dir
        self._subjects_found = None

    def get_models_to_fit(self):
        return self.models_to_fit

    def get_subjects(self):
        if not self._subjects_found:
            self._subjects_found = self._get_subjects()

        return self._subjects_found

    def profile_suitable(self):
        if not self._subjects_found:
            self._subjects_found = self._get_subjects()

        return len(self._subjects_found) > 0

    def get_subjects_count(self):
        if not self._subjects_found:
            self._subjects_found = self._get_subjects()

        return len(self._subjects_found)

    def _autoload_noise_std(self, subject_id, file_path=None):
        """Try to autoload the noise standard deviation from a noise_std file.

        Args:
            subject_id (str): the subject for which to load the noise std.
            file_path (str): optionally provide the exact file to load.

        Returns:
            float or None: a float if a float could be loaded from a file noise_std, else nothing.
        """
        file_path = file_path or os.path.join(self._root_dir, subject_id, 'noise_std')
        if os.path.isfile(file_path):
            with open(file_path, 'r') as f:
                try:
                    return float(f.read())
                except ValueError:
                    return None
        return None

    def _get_subjects(self):
        """Get the matching subjects from the given root dir.

        This is the only function that should be implemented by implementing classes to get up and running.

        Returns:
            list of SubjectInfo: the information about the found subjects
        """
        return []

    def _get_subject_output_dir(self, subject_id):
        """Helper function for generating the output directory for a subject.

        Args:
            subject_id (str): the id of the subject to use

        Returns:
            str: the path for the output directory
        """
        dir_items = [self._root_dir, subject_id, self.output_base_dir]
        if self.output_sub_dir:
            dir_items.append(self.output_sub_dir)
        return os.path.join(*dir_items)


class SubjectInfo(object):

    @property
    def subject_id(self):
        """Get the ID of this subject.

        Returns:
            str: the id of this subject
        """
        return ''

    @property
    def output_dir(self):
        """Get the output folder for this subject.

        Returns:
            str: the output folder
        """
        return ''

    def get_protocol_loader(self):
        """Get the protocol to use, or a filename of a protocol file to load.

        Returns:
            ProtocolLoader: the protocol loader
        """

    def get_dwi_info(self):
        """Get the diffusion weighted image information.

        Returns:
            (img, header) tuple or str: either a string with the filename of the image to load or the actual
                image itself with a header in a tuple.
        """

    def get_mask_filename(self):
        """Get the filename of the mask to load.

        Returns:
            str: the filename of the mask to load
        """

    def get_gradient_deviations(self):
        """Get a possible gradient deviation image to use.

        Returns:
            str: the filename of the gradient deviations to use, None if not applicable.
        """
        return None

    def get_noise_std(self):
        """Get the noise standard deviation to use during fitting.

        Returns:
            The noise std to use. This can either be a value, None, or the string 'auto'. If auto we try to auto detect it.
            If None it is set to 1.0
        """
        return 'auto'


class SimpleSubjectInfo(SubjectInfo):

    def __init__(self, subject_id, dwi_fname, protocol_loader, mask_fname, output_dir, gradient_deviations=None,
                 noise_std='auto'):
        """This class contains all the information about found subjects during batch fitting.

        It is returned by the method get_subjects() from the class BatchProfile.

        Args:
            subject_id (str): the subject id
            dwi_fname (str): the filename with path to the dwi image
            protocol_loader (ProtocolLoader): the protocol loader that can load us the protocol
            mask_fname (str): the filename of the mask to load. If None a mask is auto generated.
            output_dir (str): the output directory
            gradient_deviations (str) if given, the path to the gradient deviations
            noise_std (float, str): if given, either 'auto' for automatic noise detection or a float with the noise STD
                to use during fitting.
        """
        self._subject_id = subject_id
        self._dwi_fname = dwi_fname
        self._protocol_loader = protocol_loader
        self._mask_fname = mask_fname
        self._output_dir = output_dir
        self._gradient_deviations = gradient_deviations
        self._noise_std = noise_std

        if self._mask_fname is None:
            self._mask_fname = os.path.join(self.output_dir, 'auto_generated_mask.nii.gz')

    @property
    def subject_id(self):
        return self._subject_id

    @property
    def output_dir(self):
        return self._output_dir

    def get_subject_id(self):
        return self.subject_id

    def get_protocol_loader(self):
        return self._protocol_loader

    def get_dwi_info(self):
        return self._dwi_fname

    def get_mask_filename(self):
        if not os.path.isfile(self._mask_fname):
            logger = logging.getLogger(__name__)
            logger.info('Creating a brain mask for subject {0}'.format(self.subject_id))

            protocol = self.get_protocol_loader().get_protocol()
            create_write_median_otsu_brain_mask(self.get_dwi_info(), protocol, self._mask_fname)

        return self._mask_fname

    def get_gradient_deviations(self):
        return self._gradient_deviations

    def get_noise_std(self):
        return self._noise_std


class BatchSubjectSelection(object):

    def get_selection(self, subjects):
        """Get the selection of subjects from the given list of subjects.

        Args:
            subjects (list of SubjectInfo): the list of subjects from which we can choose which one to process

        Returns:
            list of SubjectInfo: the given list or a subset of the given list with the subjects to process.
        """
        pass


class AllSubjects(BatchSubjectSelection):
    """Selects all subjects for use in the processing"""

    def get_selection(self, subjects):
        return subjects


class SelectedSubjects(BatchSubjectSelection):

    def __init__(self, subject_ids=None, indices=None):
        """Only process the selected subjects.

        This method allows either a selection by index (unsafe for the order may change) or by subject name/ID (more
        safe in general). Both are used simultaneously.

        Args:
            subject_ids (list of str): the list of names of subjects to process
            indices (list/tuple of int): the list of indices of subjects we wish to process
        """
        self.subject_ids = subject_ids or []
        self.indices = indices or []

    def get_selection(self, subjects):
        return_list = []
        for ind, subject in enumerate(subjects):
            if ind in self.indices or subject.subject_id in self.subject_ids:
                return_list.append(subject)
        return return_list


class BatchFitProtocolLoader(ProtocolLoader):

    def __init__(self, base_dir, protocol_fname=None, protocol_options=None, bvec_fname=None, bval_fname=None):
        """A simple protocol loader for loading a protocol from a protocol file or bvec/bval files.

        This either loads the protocol file if present, or autoloads the protocol using the auto_load_protocol
        from the protocol module.
        """
        super(BatchFitProtocolLoader, self).__init__()
        self._base_dir = base_dir
        self._protocol_fname = protocol_fname
        self._bvec_fname = bvec_fname
        self._bval_fname = bval_fname
        self._protocol_options= protocol_options

    def get_protocol(self):
        super(BatchFitProtocolLoader, self).get_protocol()

        if self._protocol_fname and os.path.isfile(self._protocol_fname):
            return load_protocol(self._protocol_fname)

        return protocols.auto_load_protocol(self._base_dir, protocol_options=self._protocol_options,
                                            bvec_fname=self._bvec_fname, bval_fname=self._bval_fname)


class BatchFitSubjectOutputInfo(object):

    def __init__(self, subject_info, output_path, mask_name, model_name):
        """This class is used in conjunction with the function run_function_on_batch_fit_output().

        Args:
            subject_info (SubjectInfo): the information about the subject before batch fitting
            output_path (str): the full path to the directory with the maps
            mask_name (str): the name of the mask (not a path)
            model_name (str): the name of the model (not a path)
        """
        self.subject_info = subject_info
        self.output_path = output_path
        self.mask_name = mask_name
        self.model_name = model_name
        self.available_map_names = [split_image_path(v)[1] for v in glob.glob(os.path.join(self.output_path, '*.nii*'))]


class BatchFitOutputInfo(object):

    def __init__(self, data_folder, batch_profile=None, subjects_selection=None):
        """Single point of information about batch fitting output.

        Args:
            data_folder (str): The data folder with the output files
            batch_profile (BatchProfile class or str): the batch profile to use, can also be the name
                of a batch profile to load. If not given it is auto detected.
            subjects_selection (BatchSubjectSelection): the subjects to use for processing.
                If None all subjects are processed.
        """
        self._data_folder = data_folder
        self._batch_profile = batch_profile_factory(batch_profile, data_folder)
        self._subjects_selection = subjects_selection or AllSubjects()
        self._subjects = self._subjects_selection.get_selection(self._batch_profile.get_subjects())
        self._subjects_dirs = {subject_info.subject_id: subject_info.output_dir for subject_info in self._subjects}
        self._mask_paths = {}

    def get_available_masks(self):
        """Searches all the subjects and lists the unique available masks.

        Returns:
            list: the list of the available maps. Not all subjects may have the available mask.
        """
        s = set()
        for subject_id, path in self._subjects_dirs.items():
            masks = (p for p in os.listdir(path) if os.path.isdir(os.path.join(path, p)))
            list(map(s.add, masks))
        return list(sorted(list(s)))

    def get_path_to_mask_per_subject(self, mask_name, error_on_missing_mask=False):
        """Get for every subject the path to the results calculated with given mask name.

        If a subject does not have that mask_name it is either skipped or an error is raised, depending on the setting
        error_on_missing_mask.

        Args:
            mask_name (str): the name of the mask we return the path to per subject
            error_on_missing_mask (boolean): if we don't have the mask for one subject should we raise an error or skip
                the subject?

        Returns:
            dict: per subject ID the path to the mask
        """
        if mask_name in self._mask_paths:
            return self._mask_paths[mask_name]

        paths = {}
        for subject_id, path in self._subjects_dirs.items():
            mask_dir = os.path.join(path, mask_name)
            if os.path.isdir(mask_dir):
                paths.update({subject_id: mask_dir})
            else:
                if error_on_missing_mask:
                    raise ValueError('Missing the choosen mask "{0}" for subject "{1} '
                                     'and error_on_missing_mask is True"'.format(mask_name, subject_id))

        self._mask_paths.update({mask_name: paths})
        return paths

    def subject_output_info_generator(self, mask_name, error_on_missing_mask=False):
        """Generates for every subject an output info object which contains all relevant information about the subject.

        If a subject does not have that mask_name it is either skipped or an error is raised, depending on the setting
        error_on_missing_mask.

        Args:
            mask_name (str): the name of the mask we return the path to per subject
            error_on_missing_mask (boolean): if true, if we don't have the given mask for a subject we raise an error.
                If false, if we don't have a mask for a subject we do nothing.

        Returns:
            generator: returns an BatchFitSubjectOutputInfo per subject
        """
        mask_paths = self.get_path_to_mask_per_subject(mask_name, error_on_missing_mask)

        for subject_info in self._subjects:
            if subject_info.subject_id in mask_paths:
                mask_path = mask_paths[subject_info.subject_id]

                for model_name in os.listdir(mask_path):
                    output_path = os.path.join(mask_path, model_name)
                    if os.path.isdir(output_path):
                        yield BatchFitSubjectOutputInfo(subject_info, output_path, mask_name, model_name)
            else:
                if error_on_missing_mask:
                    raise ValueError('Missing the choosen mask "{0}" for subject "{1} '
                                     'and error_on_missing_mask is True"'.format(mask_name, subject_info.subject_id))


def run_function_on_batch_fit_output(data_folder, func, batch_profile=None, subjects_selection=None):
    """Run a function on the output of a batch fitting routine.

    This enables you to run a function on every model output from every subject. The python function should accept
    as single argument an instance of the class BatchFitSubjectOutputInfo.

    Args:
        data_folder (str): The data folder with the output files
        func (python function): the python function we should call for every map and model.
            This should accept as single parameter a BatchFitSubjectOutputInfo.
        batch_profile (BatchProfile class or str): the batch profile to use, can also be the name
            of a batch profile to load. If not given it is auto detected.
        subjects_selection (BatchSubjectSelection): the subjects to use for processing.
            If None all subjects are processed.

    Returns:
        dict: indexed by subject->model_name->mask_name, values are the return values of the user function
    """
    output_info = BatchFitOutputInfo(data_folder, batch_profile, subjects_selection=subjects_selection)
    mask_names = output_info.get_available_masks()

    results = AutoDict()
    for mask_name in mask_names:
        for subject in output_info.subject_output_info_generator(mask_name):
            subject_id = subject.subject_info.subject_id
            model_name = subject.model_name

            results[subject_id][model_name][mask_name] = func(subject)

    return results.to_normal_dict()


def batch_profile_factory(batch_profile, data_folder):
    """Wrapper function for getting a batch profile.

    Args:
        batch_profile (None, string or BatchProfile): indication of the batch profile to load.
            If a string is given it is loaded from the users home folder. Else the best matching profile is returned.
        data_folder (str): the data folder we want to use the batch profile on.

    Returns:
        If the given batch profile is None we return the output from get_best_batch_profile(). If batch profile is
        a string we load it from the batch profiles loader. Else we return the input.
    """
    if batch_profile is None:
        batch_profile = get_best_batch_profile(data_folder)
    elif isinstance(batch_profile, string_types):
        batch_profile = BatchProfilesLoader().load(batch_profile)

    batch_profile.set_root_dir(data_folder)
    return batch_profile


def get_best_batch_profile(data_folder):
    """Get the batch profile that best matches the given directory.

    Args:
        data_folder (str): the directory for which to get the best batch profile.

    Returns:
        BatchProfile: the best matching batch profile.
    """
    profile_loader = BatchProfilesLoader()
    crawlers = [profile_loader.load(c) for c in profile_loader.list_all()]

    best_crawler = None
    best_subjects_count = 0
    for crawler in crawlers:
        crawler.set_root_dir(data_folder)
        if crawler.profile_suitable():
            tmp_count = crawler.get_subjects_count()
            if tmp_count > best_subjects_count:
                best_crawler = crawler
                best_subjects_count = tmp_count

    return best_crawler


def collect_batch_fit_output(data_folder, output_dir, batch_profile=None, subjects_selection=None,
                             mask_name=None, symlink=True):
    """Load from the given data folder all the output files and put them into the output directory.

    If there is more than one mask file available the user has to choose which mask to use using the mask_name
    keyword argument. If it is not given an error is raised.

    The results for the chosen mask it placed in the output folder per subject. Example:
        <output_dir>/<subject_id>/<results>

    Args:
        data_folder (str): The data folder with the output files
        output_dir (str): The path to the output folder where all the files will be put.
        batch_profile (BatchProfile class or str): the batch profile to use, can also be the name
            of a batch profile to load. If not given it is auto detected.
        subjects_selection (BatchSubjectSelection): the subjects to use for processing.
            If None all subjects are processed.
        mask_name (str): the mask to use to get the output from
        symlink (boolean): only available under Unix OS's. Creates a symlink instead of copying.
    """
    output_info = BatchFitOutputInfo(data_folder, batch_profile, subjects_selection=subjects_selection)
    mask_names = output_info.get_available_masks()
    if len(mask_names) > 1:
        if mask_name is None:
            raise ValueError('There are results of more than one mask. '
                             'Please choose one out of ({}) '
                             'using the \'mask_name\' keyword.'.format(', '.join(mask_names)))
    else:
        mask_name = mask_names[0]

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    mask_paths = output_info.get_path_to_mask_per_subject(mask_name)

    for subject_id, mask_path in mask_paths.items():
        subject_out = os.path.join(output_dir, subject_id)

        if os.path.exists(subject_out) or os.path.islink(subject_out):
            if os.path.islink(subject_out):
                os.unlink(subject_out)
            else:
                shutil.rmtree(output_dir)

        if symlink:
            os.symlink(mask_path, subject_out)
        else:
            shutil.copytree(mask_path, subject_out)
