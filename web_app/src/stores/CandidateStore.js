// CandidateStore will hold candidates
import { dispatcher } from 'AppDispatcher';
import { mergeIntoStore, createStore } from 'utils/createStore';
import { CandidateConstants } from 'constants/Constants';
import { each } from 'underscore';

const _candidates = {};

/**
 * add data into store via mergeIntoStore
 * @param {Object} data data from server to merge
 */
function add (data) {
    mergeIntoStore(_candidates, data);
}

/**
 * add an array of offices to the store
 * @param {Array} officeArray array of offices to be added to the store
 */
function addArray (candidates) {
    candidates.forEach(office => add(office));
}

const CandidateStore = createStore({
    /**
     * get ballot by id
     * @param  {String} ballot_id id of ballot
     * @return {Object} ballot data item
     */
    get (id) {
        return _candidates[id];
    },

    /**
     * @return {Array} array of Ballot Data
     */
    toArray () {
        let _candidateArray = [];
        each(_candidates, (val, key) =>
            _candidateArray.push(_candidates[key])
        );
        return _candidateArray;
    }
});

export default CandidateStore;

dispatcher.register ( action => {
    switch (action.actionType) {
        case CandidateConstants.CANDIDATES_DONE_LOADING:
            addArray(action.offices);
            CandidateStore.emitChange();
            break;

        default:
            // do nothing
            break;
    }
});
